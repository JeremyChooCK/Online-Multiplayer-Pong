// const gameSocket = new WebSocket('wss://localhost/ws/game/');
const paddle1 = document.getElementById('paddle1');
const paddle2 = document.getElementById('paddle2');
const ball = document.getElementById('ball');
const player1Score = document.getElementById('player1Score');
const player2Score = document.getElementById('player2Score');
const startButton = document.getElementById('startButton');
const joinButton = document.getElementById('joinButton');
const messageBox = document.getElementById('messageBox');
let gameSocket;

joinButton.addEventListener('click', async function() {
    gameSocket = new WebSocket('wss://localhost/ws/game/');

    gameSocket.onopen = function() {
        messageBox.innerText = "Connected. Waiting for another player...";
    };

    gameSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'game_starting') {
            messageBox.innerText = data.message;
        } else if (data.type === 'notify') {
            messageBox.innerText = data.message;
        } else if (data.ball_position) {
            ball.style.left = `${data.ball_position.x}%`;
            ball.style.top = `${data.ball_position.y}%`;
        }

        if (data.paddle_positions) {
            paddle1.style.top = `${data.paddle_positions.player1}%`;
            paddle2.style.top = `${data.paddle_positions.player2}%`;
        }

        if (data.score) {
            player1Score.textContent = data.score.player1;
            player2Score.textContent = data.score.player2;
        }

        if (data.type === 'game_over') {
            alert(data.message);
            gameSocket.close();
        }
    };

    gameSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        messageBox.innerText = "Connection error. Please refresh to try again.";
    };

    gameSocket.onclose = function() {
        console.log('WebSocket closed unexpectedly.');
        messageBox.innerText = "Disconnected. Please refresh to join again.";
    };
});

function getPaddlePosition(key) {
    const pongGame = document.getElementById('pongGame');
    const paddle = document.querySelector('.paddle');

    // Calculate the paddle's height as a percentage of its container
    const paddleHeightPx = parseFloat(window.getComputedStyle(paddle).height);
    const pongGameHeightPx = parseFloat(window.getComputedStyle(pongGame).height);
    const paddleHeightPercent = (paddleHeightPx / pongGameHeightPx) * 100;

    // Current top position as a percentage
    const currentPercent = parseFloat(paddle.style.top.replace('%', '')) || 50;

    // Determine the percentage step for each key press
    const stepPercent = (60 / pongGameHeightPx) * 100;  // Using a fixed step of 60 pixels converted to percentage

    let newPercent = currentPercent;
    if (key === 'ArrowUp') {
        newPercent = Math.max(currentPercent - stepPercent, 0);  // Ensure the paddle doesn't go above the top edge
    } else if (key === 'ArrowDown') {
        newPercent = Math.min(currentPercent + stepPercent, 100 - paddleHeightPercent);  // Adjust for paddle height
    }

    paddle.style.top = `${newPercent}%`;  // Update the DOM using percentages
    return newPercent;  // Send this to the server
}


let isUpPressed = false;
let isDownPressed = false;

document.addEventListener('keydown', function(event) {
    if (event.key === 'ArrowUp') {
        isUpPressed = true;
    } else if (event.key === 'ArrowDown') {
        isDownPressed = true;
    }
});

document.addEventListener('keyup', function(event) {
    if (event.key === 'ArrowUp') {
        isUpPressed = false;
    } else if (event.key === 'ArrowDown') {
        isDownPressed = false;
    }
});

let lastUpdateTime = 0;
const updateInterval = 50; // Update every 50 milliseconds

function updatePaddlePosition(timestamp) {
    if (timestamp - lastUpdateTime > updateInterval) {
        if (isUpPressed) {
            const newPosition = getPaddlePosition('ArrowUp');
            gameSocket.send(JSON.stringify({
                action: 'move_paddle',
                position: newPosition,
                user_id: 1
            }));
        }
        if (isDownPressed) {
            const newPosition = getPaddlePosition('ArrowDown');
            gameSocket.send(JSON.stringify({
                action: 'move_paddle',
                position: newPosition,
                user_id: 1
            }));
        }
        lastUpdateTime = timestamp;
    }
    requestAnimationFrame(updatePaddlePosition);
}

requestAnimationFrame(updatePaddlePosition);



function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}