from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import re
import os
from datetime import datetime

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'signin'

# directories
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)

# Tables
followers_association = db.Table('followers_association',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

follow_requests = db.Table('follow_requests',
    db.Column('requester_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('requested_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

# Table for group members
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(255))


    # Relationship for followers
    followers = db.relationship('User', 
                                secondary=followers_association,
                                primaryjoin=(id == followers_association.c.followed_id),
                                secondaryjoin=(id == followers_association.c.follower_id),
                                backref=db.backref('following', lazy='dynamic'),
                                lazy='dynamic')

    follow_requests = db.relationship('User', 
                                      secondary=follow_requests,
                                      primaryjoin=(id == follow_requests.c.requested_id),
                                      secondaryjoin=(id == follow_requests.c.requester_id),
                                      backref=db.backref('sent_requests', lazy='dynamic'),
                                      lazy='dynamic')

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    # Relationship for groups
    groups = db.relationship('Group', secondary=group_members, backref=db.backref('members', lazy='dynamic'))

    # User methods
    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        return self.following.filter(followers_association.c.followed_id == user.id).count() > 0

    def send_follow_request(self, user):
        if not self.has_sent_request(user):
            self.sent_requests.append(user)

    def has_sent_request(self, user):
        return self.sent_requests.filter(follow_requests.c.requested_id == user.id).count() > 0

    def accept_follow_request(self, user):
        if self.has_received_request(user):
            self.follow_requests.remove(user)
            self.followers.append(user)

    def decline_follow_request(self, user):
        if self.has_received_request(user):
            self.follow_requests.remove(user)

    def has_received_request(self, user):
        return self.follow_requests.filter(follow_requests.c.requester_id == user.id).count() > 0

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(255))
    video = db.Column(db.String(255))
    likes = db.relationship('User', secondary='post_likes', backref=db.backref('liked_posts', lazy='dynamic'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)

    def like_count(self):
        return len(self.likes)

    def comment_count(self):
        return self.comments.count()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic')) # loads relation lazily

post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
) 

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref=db.backref('created_groups', lazy='dynamic'))
    posts = db.relationship('Post', backref='group', lazy='dynamic')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Validation for pw
def validate_password(password):
    if (len(password) >= 8 and
        re.search(r"[a-z]", password) and
        re.search(r"[A-Z]", password) and
        re.search(r"\d", password)):
        return True
    return False

# Image resizing
def resize_and_crop(image_path, size, aspect_ratio='square'):
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if aspect_ratio == 'square':
            
            width, height = img.size
            new_size = min(width, height)
            
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2
            
            img = img.crop((left, top, right, bottom))
        elif aspect_ratio == '16:9':
            
            aspect_ratio_original = img.width / img.height
            aspect_ratio_target = 16 / 9
            
            if aspect_ratio_original > aspect_ratio_target:
                # Original image is wider, crop the width
                new_width = int(img.height * aspect_ratio_target)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            elif aspect_ratio_original < aspect_ratio_target:
                # Original image is taller, crop the height
                new_height = int(img.width / aspect_ratio_target)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
        
        img = img.resize(size, Image.LANCZOS)
        img.save(image_path)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

# Check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    return redirect(url_for('signin'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('profile', username=current_user.username))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))

        if not validate_password(password):
            flash('Password does not meet the criteria.', 'error')
            return redirect(url_for('signup'))

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already registered.', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. Please sign in.', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('profile', username=current_user.username))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Signed in successfully!', 'success')
            return redirect(url_for('profile', username=user.username))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('signin.html')

@app.route('/signout')
@login_required
def signout():
    logout_user()
    flash('Signed out successfully.', 'success')
    return redirect(url_for('signin'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Check if the current user is the owner of the profile
    is_own_profile = current_user.username == username
    is_follower = current_user.is_following(user)
    
    if is_own_profile or is_follower:
        posts = user.posts.filter(Post.group_id == None).order_by(Post.timestamp.desc()).all()
    else:
        posts = []

    groups = user.groups

    return render_template('profile.html', user=user, posts=posts, 
                           is_own_profile=is_own_profile, is_follower=is_follower,
                           groups=groups)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.bio = request.form['bio']
        
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                filename = secure_filename(file.filename)
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics', filename)
                file.save(file_path)
                
                resize_and_crop(file_path, (320, 180), aspect_ratio='16:9')
                
                current_user.profile_pic = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_profile.html', user=current_user)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
        return render_template('search_results.html', users=users, query=search_query)
    return render_template('search.html')

@app.route('/send_follow_request/<int:user_id>')
@login_required
def send_follow_request(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    if user_to_follow == current_user:
        flash('You cannot follow yourself.', 'error')
    elif current_user.is_following(user_to_follow):
        flash('You are already following this user.', 'error')
    else:
        current_user.send_follow_request(user_to_follow)
        db.session.commit()
        flash('Follow request sent.', 'success')
    return redirect(url_for('profile', username=user_to_follow.username))

@app.route('/accept_follow_request/<int:user_id>')
@login_required
def accept_follow_request(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.has_received_request(user):
        current_user.accept_follow_request(user)
        db.session.commit()
        flash('Follow request accepted.', 'success')
    else:
        flash('No follow request from this user.', 'error')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/decline_follow_request/<int:user_id>')
@login_required
def decline_follow_request(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.has_received_request(user):
        current_user.decline_follow_request(user)
        db.session.commit()
        flash('Follow request declined.', 'success')
    else:
        flash('No follow request from this user.', 'error')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user_to_unfollow = User.query.get_or_404(user_id)
    if current_user.is_following(user_to_unfollow):
        current_user.unfollow(user_to_unfollow)
        db.session.commit()
        flash('You have unfollowed this user.', 'success')
    else:
        flash('You are not following this user.', 'error')
    return redirect(url_for('profile', username=user_to_unfollow.username))

@app.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    followers = user.followers.all()
    return render_template('followers.html', user=user, followers=followers)

@app.route('/following/<username>')
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    following = user.following.all()
    return render_template('following.html', user=user, following=following)



@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        content = request.form['content']
        image = request.files.get('image')
        video = request.files.get('video')
        group_id = request.form.get('group_id')

        post = Post(content=content, author=current_user)

        if group_id:
            group = Group.query.get(group_id)
            if group and current_user in group.members:
                post.group = group
            else:
                flash('You cannot post in this group.', 'error')
                return redirect(url_for('profile', username=current_user.username))

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            image.save(image_path)
            resize_and_crop(image_path, (800, 450), aspect_ratio='16:9')
            post.image = filename

        if video and allowed_file(video.filename):
            filename = secure_filename(video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            video.save(video_path)
            post.video = filename

        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        
        if group_id:
            return redirect(url_for('view_group', group_id=group_id))
        else:
            return redirect(url_for('profile', username=current_user.username))

    groups = current_user.groups
    return render_template('create_post.html', groups=groups)

@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if the post belongs to a group
    if post.group:
        # If it's a group post, check if the current user is a member of the group
        if current_user not in post.group.members:
            flash('You must be a member of the group to view this post.', 'error')
            return redirect(url_for('view_group', group_id=post.group.id))
    else:
        # If it's not a group post, check if the current user is following the post author
        if current_user != post.author and not current_user.is_following(post.author):
            flash('You need to follow the user to view this post.', 'error')
            return redirect(url_for('profile', username=post.author.username))

    return render_template('view_post.html', post=post)

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user not in post.likes:
        post.likes.append(current_user)
        db.session.commit()
    return jsonify({'likes': len(post.likes)})

@app.route('/unlike/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user in post.likes:
        post.likes.remove(current_user)
        db.session.commit()
    return jsonify({'likes': len(post.likes)})

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, user=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        existing_group = Group.query.filter_by(name=name).first()
        if existing_group:
            flash('A group with this name already exists.', 'error')
            return redirect(url_for('create_group'))
        
        new_group = Group(name=name, description=description, creator=current_user)
        new_group.members.append(current_user)
        db.session.add(new_group)
        db.session.commit()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('view_group', group_id=new_group.id))
    
    return render_template('create_group.html')

@app.route('/group/<int:group_id>')
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    is_member = current_user in group.members

    if is_member:
        posts = group.posts.order_by(Post.timestamp.desc()).all()
    else:
        posts = []

    return render_template('view_group.html', group=group, posts=posts, is_member=is_member)

@app.route('/join_group/<int:group_id>')
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        group.members.append(current_user)
        db.session.commit()
        flash('You have joined the group successfully!', 'success')
    else:
        flash('You are already a member of this group.', 'info')
    return redirect(url_for('view_group', group_id=group_id))

@app.route('/leave_group/<int:group_id>')
@login_required
def leave_group(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user in group.members:
        group.members.remove(current_user)
        db.session.commit()
        flash('You have left the group.', 'success')
    else:
        flash('You are not a member of this group.', 'error')
    return redirect(url_for('view_group', group_id=group_id))

@app.route('/create_group_post/<int:group_id>', methods=['GET', 'POST'])
@login_required
def create_group_post(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        flash('You must be a member of the group to create a post.', 'error')
        return redirect(url_for('view_group', group_id=group_id))

    if request.method == 'POST':
        content = request.form['content']
        image = request.files.get('image')
        video = request.files.get('video')

        post = Post(content=content, author=current_user, group=group)

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            image.save(image_path)
            resize_and_crop(image_path, (800, 450), aspect_ratio='16:9')
            post.image = filename

        if video and allowed_file(video.filename):
            filename = secure_filename(video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            video.save(video_path)
            post.video = filename

        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('view_group', group_id=group_id))

    return render_template('create_group_post.html', group=group)

@app.route('/search_groups', methods=['GET', 'POST'])
@login_required
def search_groups():
    if request.method == 'POST':
        search_query = request.form['search_query']
        groups = Group.query.filter(Group.name.ilike(f'%{search_query}%')).all()
        return render_template('search_groups_results.html', groups=groups, query=search_query)
    return render_template('search_groups.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)