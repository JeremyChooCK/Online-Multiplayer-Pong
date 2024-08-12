const gameSocket = new WebSocket('wss://localhost/ws/game/');
const paddle1 = document.getElementById('paddle1');
const paddle2 = document.getElementById('paddle2');
const ball = document.getElementById('ball');
const player1Score = document.getElementById('player1Score');
const player2Score = document.getElementById('player2Score');
const startButton = document.getElementById('startButton');

gameSocket.onmessage = function(event) {
    // console.log("Message received: ", event.data);
    const data = JSON.parse(event.data);
    // console.log("ball_position: ", data.ball_position);
    if (data.ball_position) {
        ball.style.left = `${data.ball_position.x}%`;
        ball.style.top = `${data.ball_position.y}%`;
    }

    if (data.paddle_positions) {
        // Assuming 'player1' and 'player2' are the keys for paddle positions
        if (data.paddle_positions.player1 !== undefined) {
            paddle1.style.top = `${data.paddle_positions.player1}%`;
            console.log("Paddle 1 position: ", data.paddle_positions.player1);
        }
        if (data.paddle_positions.player2 !== undefined) {
            paddle2.style.top = `${data.paddle_positions.player2}%`;
            // console.log("Paddle 2 position: ", data.paddle_positions.player2);
        }
    }

    // Update scores
    if (data.score) {
        player1Score.textContent = data.score.player1;
        player2Score.textContent = data.score.player2;
    }
    // Handling the game over message
    if (data.type === 'game_over') {
        console.log("Data received: ", data);
        alert(data.message);  // Display the game over message in an alert
        const winMessage = document.getElementById('winMessage');
        if (winMessage) {
            winMessage.textContent = data.message;  // Optionally display it on the webpage
        }
        gameSocket.close();  // Close the WebSocket after the game is over
    }
};


gameSocket.onopen = function() {
    startButton.addEventListener('click', function() {
        gameSocket.send(JSON.stringify({
            'action': 'start_game',
            'user_id': 1 
        }));
    });
};

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

gameSocket.onclose = function(event) {
    console.log('WebSocket closed. If the game is over, redirect or handle post-game actions.');
    // Optionally, redirect to a different page or display any relevant UI element
};
