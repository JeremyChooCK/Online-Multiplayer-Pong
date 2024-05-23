document.addEventListener('DOMContentLoaded', checkAuthOnLoad);

function checkAuthOnLoad() {
    const accessToken = localStorage.getItem("accessToken");
    console.log("Access Token exists");
    if (accessToken) {
        try {
            const decoded = jwt_decode(accessToken);
            if (decoded && decoded.username) { // Assuming 'username' is the claim name
                document.getElementById("usernameDisplay").textContent = decoded.username;
                document.getElementById("welcomeSection").style.display = '';
                document.getElementById("logoutButton").style.display = '';
                document.getElementById("loginButton").style.display = 'none';
                document.getElementById("registerButton").style.display = 'none';
                if (decoded.profile_pic)
                    document.getElementById("profile_pic").src = decoded.profile_pic.link;
                else
                    document.getElementById("profile_pic").src = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png";
            } else {
                handleLoggedOutState();
            }
        } catch (error) {
            console.error('Error decoding token:', error);
            handleLoggedOutState();
        }
    } else {
        handleLoggedOutState();
    }
}

function handleLoggedOutState() {
    document.getElementById("welcomeSection").style.display = 'none';
    document.getElementById("logoutButton").style.display = 'none';
    document.getElementById("loginButton").style.display = '';
    document.getElementById("registerButton").style.display = '';
    document.getElementById("profile_pic").display = 'none';
}

async function postLogin() {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;
    const url = "http://127.0.0.1:8000/auth/token/";

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error('Unauthorized'); // Adjusted for consistency with your error handling
        }

        const data = await response.json();
        localStorage.setItem("accessToken", data.access);
        localStorage.setItem("refreshToken", data.refresh);

        // Update UI after login
        document.getElementById("usernameDisplay").textContent = username;
        document.getElementById("welcomeSection").style.display = '';
        document.getElementById("logoutButton").style.display = '';
        document.getElementById("loginButton").style.display = 'none';
        document.getElementById("registerButton").style.display = 'none';
        if(data.profile_picture)
            document.getElementById("profile_pic").src = data.profile_picture;
        else
            document.getElementById("profile_pic").src = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png";
        console.log(data.profile_picture);

        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        if (error.message === "Unauthorized") {
            alert("Invalid credentials");
        }
    }
}

async function loginAfterRegister(username, password) {
    const url = "http://127.0.0.1:8000/auth/token/";

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error('Unauthorized'); // Adjusted for consistency with your error handling
        }

        const data = await response.json();
        localStorage.setItem("accessToken", data.access);
        localStorage.setItem("refreshToken", data.refresh);

        // Update UI after login
        document.getElementById("usernameDisplay").textContent = username;
        document.getElementById("welcomeSection").style.display = '';
        document.getElementById("logoutButton").style.display = '';
        document.getElementById("loginButton").style.display = 'none';
        document.getElementById("registerButton").style.display = 'none';

        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        if (error.message === "Unauthorized") {
            alert("Invalid credentials");
        }
    }
}

async function postRegister() {
    const username = document.getElementById("newUsernameInput").value;
    const password = document.getElementById("newPasswordInput").value;
    const confirmPassword = document.getElementById("confirmPasswordInput").value;
    // if (password !== confirmPassword) {
    //     alert("Passwords do not match.");
    //     return;
    // }
    const url = "http://127.0.0.1:8000/auth/register/";
    
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            console.log(response);
            throw new Error('Username already exists'); // Adjusted for consistency with your error handling
        }

        const data = await response.json();
        console.log('successfully registered');
        loginAfterRegister(username, password);
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        if (error.message === "Username already exists") {
            alert("Username already exists");
        }
    }

}

async function Logout() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    document.getElementById("usernameDisplay").textContent = '';
    document.getElementById("welcomeSection").style.display = 'none';
    document.getElementById("loginButton").style.display = '';
    document.getElementById("registerButton").style.display = '';
    document.getElementById("logoutButton").style.display = 'none';
    document.getElementById("profile_pic").display = 'none';
    document.getElementById("profile_pic").src = "";
}

async function verifyTokenAndExecute(callback) {
    let accessToken = localStorage.getItem("accessToken");
    if (!accessToken) {
        alert("You are not logged in.");
        return;
    }

    // Decode the token without verifying to check expiry
    const decoded = jwt_decode(accessToken);
    const now = Date.now() / 1000; // Current time in seconds since epoch

    // If token is about to expire in less than 30 seconds, refresh it
    if (decoded.exp && decoded.exp - now < 30) {
        accessToken = await refreshAccessToken(); // Refresh the token
        if (!accessToken) {
            alert("Session expired. Please log in again.");
            return; // Exit if no new token is obtained
        }
    }

    const url = "http://127.0.0.1:8000/auth/token/verify/"; // Adjust this to your actual token verification endpoint

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            },
            body: JSON.stringify({ token: accessToken })
        });

        if (response.ok) {
            callback(); // Proceed with the callback if the token is valid
        } else {
            throw new Error('Failed to verify token');
        }
    } catch (error) {
        console.error('Error verifying token:', error);
        alert("An error occurred. Please try again.");
    }
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refreshToken");
    if (!refreshToken) {
        console.error("No refresh token available.");
        return;
    }

    const url = "http://127.0.0.1:8000/auth/token/refresh/";  // Your API endpoint for refreshing tokens

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("accessToken", data.access);  // Update the access token
            console.log("Access token refreshed.");
            return data.access;
        } else {
            throw new Error('Failed to refresh access token');
        }
    } catch (error) {
        console.error('Error refreshing access token:', error);
        alert("Session expired. Please log in again.");
        // Optionally redirect to login or clear session
    }
}

function redirectToOAuthProvider() {
    const authUrl = "https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-9b0fa67cf4ac001dac948db1c08b417156de148160cb998b92520a9e9bbaef2b&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fauth%2Foauth&response_type=code";
    console.log('Auth URL:', authUrl);

    window.location.href = authUrl; // This will redirect the user to the OAuth provider
}