# RYM Clone

#### Video Demo: <URL HERE>

#### Environment Variables Configuration

To make this project work, you need to configure some environment variables.

1. Rename the `.env.example` file to `.env`.
2. Enter your API keys obtained from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).

CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret

#### Description:

## Introduction

This project is a simplified clone of the popular website "Rate Your Music," tailored to focus on user reviews, music genres, and album information. The application, designed with a clean and straightforward user interface, provides users with the ability to explore various music genres, access detailed album and artist information, and submit their own ratings. Due to certain limitations imposed by the Spotify API, some features present in the original "Rate Your Music" site are missing. Nonetheless, the project serves as an effective platform for users to engage with music content in a meaningful way.

## Key Features

### 1. **Homepage with User Reviews**

The homepage of the application is dedicated to showcasing reviews submitted by premium users. These reviews are tracked using an SQLite database, which stores information such as the review content, user details, and associated albums. The database allows for efficient retrieval and management of review data, ensuring that only premium users' reviews are displayed on the homepage. This feature provides insights into various albums and artists, offering other users a glimpse of popular or critically acclaimed music. The reviews are listed in an easy-to-navigate format, allowing users to browse through opinions and discover new music based on community feedback.

### 2. **Genres Page**

The Genres page serves as a gateway to exploring music categorized by genre. Users can select a genre of interest and be directed to a list of albums and playlists associated with that genre. This feature is especially useful for users looking to dive deeper into specific types of music, whether it's rock, jazz, electronic, or any other genre. Each genre page is dynamically populated with content fetched from the Spotify API, ensuring that users have access to a diverse range of music within their chosen category.

### 3. **Albums, Playlists and Artists Information**

Users can access detailed information about albums, playlists, and artists. Each album page provides key details such as release date, tracklist, and album artwork. Similarly, artist pages offer information on the artist's discography, biography, and related artists. This feature is designed to enrich the user experience by offering comprehensive data on the music they are interested in.

### 4. **Community Favorites**

The application features a dedicated page for displaying albums that have been rated by users. This page highlights the most popular or critically acclaimed albums within the user community, providing a quick reference for anyone looking to explore highly-rated music. The ratings are aggregated and displayed in a user-friendly format, making it easy to discover new and interesting albums based on community feedback.

### 5. **User Authentication**

To enhance user engagement, the application includes user authentication features such as registration, login, and sign-out. These features ensure that users can create personal accounts, submit reviews, and rate albums. The authentication process is designed to be secure and straightforward, allowing users to easily manage their accounts and interact with the platform.

## Technologies Used

### Backend: Python, Flask, and SQLite

The backend of the application is built using Python and Flask, with SQLite being used for the database. SQLite is chosen for its simplicity and ease of use, making it an ideal choice for managing data such as user reviews, user details, and other essential information.

- **Flask:** Flask handles the routing, server-side logic, and interaction with the Spotify API. It is also responsible for managing user sessions, handling authentication, and processing data to be displayed on the front end.
- **Python:** Python's extensive library support and simplicity make it an ideal choice for the backend. It is used to interact with the Spotify API, manage data processing, and handle various server-side operations.
- **SQLite:** SQLite is used to manage and store user reviews, user details, and other related data. It provides a lightweight, yet powerful, solution for handling the application's database needs.

### Frontend: HTML, CSS, and JavaScript

The frontend of the application is built using basic web technologies: HTML, CSS, and a touch of JavaScript. The aim was to create a clean and functional user interface that is easy to navigate and visually appealing.

- **HTML:** HTML is used to structure the content of the web pages. It provides the basic layout for the homepage, genre pages, album information pages, and user authentication forms.
- **CSS:** CSS is used to style the web pages, ensuring that the application has a cohesive and attractive appearance. Custom CSS is applied to create a responsive design that works well on both desktop and mobile devices.
- **JavaScript:** JavaScript is used to enhance the interactivity of the application. It handles client-side logic, such as form validation and dynamic content loading, providing a smoother user experience.
