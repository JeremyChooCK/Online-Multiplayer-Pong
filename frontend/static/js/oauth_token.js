const urlParams = new URLSearchParams(window.location.search);
const accessToken = urlParams.get('access');
const refreshToken = urlParams.get('refresh');

// Store tokens in localStorage
localStorage.setItem('accessToken', accessToken);
localStorage.setItem('refreshToken', refreshToken);

// Redirect to home
window.location.href = '/';