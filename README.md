# Synapse: Social Media Platform for Scientists

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Navigating Synapse](#navigating-synapse)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [License](#license)
- [Contact](#contact)

## Introduction

Synapse is a specialized social media platform designed for scientists, researchers, and academics across all disciplines. It provides a dedicated space for professionals in scientific fields to connect, share knowledge, and collaborate on projects.

## Features

- **User Profiles**: Create and customize your profile with your research interests, publications, and professional background.
- **Social Networking**: Connect with colleagues and fellow researchers in your field and beyond.
- **Content Sharing**: Share research findings, papers, and scientific discussions through text, image, and video posts.
- **Interactions**: Engage in scientific discourse through likes, comments, and direct discussions.
- **Groups**: Create or join groups based on specific research areas or interdisciplinary topics.
- **Search Functionality**: Easily find other researchers, papers, or discussion topics.

## Getting Started

### Installation

1. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

1. Start the development server:
   ```bash
   python3 app.py
   ```

2. Open your web browser and go to `http://localhost:5000`

## Navigating Synapse

1. **Sign Up/Sign In**: 
   - Create a new account or sign in to an existing one from the homepage.

2. **Setting Up Your Profile**:
   - After signing in, click on "Edit Profile" to add your research interests, publications, and professional background.

3. **Finding and Connecting with Researchers**:
   - Use the "Search" feature in the navigation bar to find other researchers or topics.
   - Visit a user's profile and click "Connect" to send a connection request.

4. **Creating Posts**:
   - From your profile or the home page, click "Create New Post".
   - Share your research findings, papers, or start a scientific discussion. You can include text, images, or videos.

5. **Interacting with Posts**:
   - Engage with posts by clicking the "Like" button or leaving a comment.
   - Start or join discussions on research topics.

6. **Groups**:
   - Create a new group for your research area by clicking "Create Group" in the navigation bar.
   - Search for existing groups using the "Search Groups" feature.
   - Join groups related to your field of study or interdisciplinary interests.

7. **Viewing Your Feed**:
   - The home page displays posts from researchers you're connected with and groups you're a member of.

## Configuration

Key configuration settings in `app.py` include:

- `SECRET_KEY`: Used for session management
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `UPLOAD_FOLDER`: Directory for user-uploaded files
- `MAX_CONTENT_LENGTH`: Maximum allowed file size for uploads

Ensure to set appropriate values, especially when deploying to production.

## Dependencies

The following dependencies are required for Synapse:

```
alembic==1.13.2
blinker==1.8.2
click==8.1.7
Flask==3.0.3
Flask-Login==0.6.3
Flask-Migrate==4.0.7
Flask-SQLAlchemy==3.1.1
greenlet==3.0.3
itsdangerous==2.2.0
Jinja2==3.1.4
Mako==1.3.5
MarkupSafe==2.1.5
pillow==10.4.0
SQLAlchemy==2.0.31
typing_extensions==4.12.2
Werkzeug==3.0.3
```

These dependencies are listed in the `requirements.txt` file and will be installed when you run `pip install -r requirements.txt`.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Contact

For support or queries, please contact wshams@uab.edu

---

Synapse - Connecting Minds in Science
