document.addEventListener('DOMContentLoaded', checkAuthOnLoad);

let ip = "https://localhost/";

async function checkAuthOnLoad() {
    const accessToken = localStorage.getItem("accessToken");
    console.log("Access Token exists");
    if (accessToken) {
        try {
            const decoded = jwt_decode(accessToken);
            if (decoded) {
                updateUIOnLogin();
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

async function fetchUserData() {
    const ip = "https://localhost/";
    const token = localStorage.getItem("accessToken");

    try {
        const response = await fetch(ip + "auth/user_details/", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Unauthorized'); // Handle 401 Unauthorized error
            } else {
                throw new Error('Network response was not ok'); // Handle other response errors
            }
        }

        const data = await response.json();
        console.log("User Data: ", data);
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        if (error.message === "Unauthorized") {
            alert("Invalid credentials");
        } else {
            alert("An error occurred while fetching the data");
        }
    }
}

async function updateUIOnLogin() {
    document.getElementById("welcomeSection").style.display = '';
    document.getElementById("logoutButton").style.display = '';
    document.getElementById("loginButton").style.display = 'none';
    document.getElementById("registerButton").style.display = 'none';
    userData = await fetchUserData();
    if(userData.profile.profile_picture){
        document.getElementById("profile_pic").src = userData.profile.profile_picture;
        document.getElementById("usernameDisplay").textContent = userData.username;
    }
}

async function handleLoggedOutState() {
    console.log("Logged out")
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    document.getElementById("usernameDisplay").textContent = '';
    document.getElementById("welcomeSection").style.display = 'none';
    document.getElementById("loginButton").style.display = '';
    document.getElementById("registerButton").style.display = '';
    document.getElementById("logoutButton").style.display = 'none';
    document.getElementById("profile_pic").display = 'none';
    document.getElementById("profile_pic").src = "";
    document.getElementById("profile_settings").style.display = 'none';
}

async function postLogin() {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;
    const url = ip + "auth/token/";

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
        updateUIOnLogin();
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        if (error.message === "Unauthorized") {
            alert("Invalid credentials");
        }
    }
}

async function loginAfterRegister(username, password) {
    const url = ip + "auth/token/";

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
        updateUIOnLogin();
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
    const url = ip + "auth/register/";
    
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

    const url = ip + "auth/token/verify/"; // Adjust this to your actual token verification endpoint

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

    const url = ip + "auth/token/refresh/";  // Your API endpoint for refreshing tokens

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
    const authUrl = "https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-9b0fa67cf4ac001dac948db1c08b417156de148160cb998b92520a9e9bbaef2b&redirect_uri=https%3A%2F%2Flocalhost%2Fauth%2Foauth&response_type=code";
    console.log('Auth URL:', authUrl);

    window.location.href = authUrl; // This will redirect the user to the OAuth provider
}

async function loadProfile(){
    document.getElementById("profile_settings").style.display = '';
    userData = await fetchUserData();
    if(userData){
        document.getElementById("profile_page_pic").src = userData.profile.profile_picture;
        document.getElementById("profile_settings_name").textContent = userData.username;
        document.getElementById("profile_wins").textContent = userData.profile.wins;
        document.getElementById("profile_losses").textContent = userData.profile.losses;
        document.getElementById("profile_name").textContent = userData.username;
    }
}

function editName(){
    document.getElementById("profile_name").style.display = 'none';
    document.getElementById("profile_name_input").style.display = '';
    document.getElementById("profile_name_input").value = userData.username;
    document.getElementById("change_profile").style.display = '';
    document.getElementById("edit_name").style.display = 'none';
}

function cancelNameChange(){
    document.getElementById("profile_name").style.display = '';
    document.getElementById("profile_name_input").style.display = 'none';
    document.getElementById("change_profile").style.display = 'none';
    document.getElementById("edit_name").style.display = '';
}

function saveProfileChanges(){
    
}

document.getElementById('profile_page_pic').addEventListener('click', function() {
    document.getElementById('profile_page_pic_input').click();
});