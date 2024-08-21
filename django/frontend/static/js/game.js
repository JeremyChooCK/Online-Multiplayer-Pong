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
let playerNumber = null;

joinButton.addEventListener('click', async function() {
    gameSocket = new WebSocket('wss://localhost/ws/game/');

    gameSocket.onopen = function() {
        messageBox.innerText = "Connected. Waiting for another player...";
    };

    gameSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'setup') {
            playerNumber = data.player_number;
            messageBox.innerText = `You are ${playerNumber}. Waiting for other player...`;
            console.log(`Setup complete for ${playerNumber}`);
        } else if (data.type === 'game_starting') {
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
            // console.log("paddle1", paddle1.style.top, "paddle2", paddle2.style.top);
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
    const paddleNumber = playerNumber.charAt(playerNumber.length - 1);
    const paddleId = 'paddle' + paddleNumber;
    const paddle = document.getElementById(paddleId);
    // console.log("paddle:", paddleId);

    // Log the heights in pixels for debugging
    const paddleHeightPx = parseFloat(window.getComputedStyle(paddle).height);
    const pongGameHeightPx = parseFloat(window.getComputedStyle(pongGame).height);
    // console.log("Paddle Height in px:", paddleHeightPx, "Game Height in px:", pongGameHeightPx);

    // Calculate the paddle's height as a percentage of its container
    const paddleHeightPercent = (paddleHeightPx / pongGameHeightPx) * 100;
    // console.log("Paddle Height Percentage:", paddleHeightPercent);

    // Current top position as a percentage
    const currentPercent = parseFloat(paddle.style.top.replace('%', '')) || 50;
    // console.log("Current Percent Position:", currentPercent);

    // Determine the percentage step for each key press
    const stepPercent = (60 / pongGameHeightPx) * 100;  // Using a fixed step of 60 pixels converted to percentage
    // console.log("Step Percent for Movement:", stepPercent);

    let newPercent = currentPercent;
    if (key === 'ArrowUp') {
        newPercent = Math.max(currentPercent - stepPercent, 0);  // Ensure the paddle doesn't go above the top edge
        // console.log("Adjusted Percent after ArrowUp:", newPercent);
    } else if (key === 'ArrowDown') {
        newPercent = Math.min(currentPercent + stepPercent, 100 - paddleHeightPercent);  // Adjust for paddle height
        // console.log("Adjusted Percent after ArrowDown:", newPercent);
    }

    // Update the DOM using percentages
    paddle.style.top = `${newPercent}%`;  
    // console.log("Updated Paddle Position:", newPercent);

    return newPercent;  // Send this to the server
}


let isUpPressed = false;
let isDownPressed = false;

document.addEventListener('keydown', function(event) {
    // console.log("playerNumber", playerNumber);
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
            // console.log("newPosition up", newPosition);
            gameSocket.send(JSON.stringify({
                action: 'move_paddle',
                position: newPosition,
                user_id: 1
            }));
        }
        if (isDownPressed) {
            const newPosition = getPaddlePosition('ArrowDown');
            // console.log("newPosition down", newPosition);
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