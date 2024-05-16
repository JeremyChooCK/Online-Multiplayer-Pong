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
        console.log('Response data:', data);
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
async function Logout() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    document.getElementById("usernameDisplay").textContent = '';
    document.getElementById("welcomeSection").style.display = 'none';
    document.getElementById("loginButton").style.display = '';
    document.getElementById("registerButton").style.display = '';
    document.getElementById("logoutButton").style.display = 'none';
}