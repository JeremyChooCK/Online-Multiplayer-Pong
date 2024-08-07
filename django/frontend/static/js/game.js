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
    const stepPercent = (20 / document.getElementById('pongGame').offsetHeight) * 100;  // Convert pixel step to percentage of total height
    const currentPercent = parseFloat(paddle1.style.top) || 50;  // Default to 50% if not set

    let newPercent;
    if (key === 'ArrowUp') {
        newPercent = Math.max(currentPercent - stepPercent, 0);
        console.log(`ArrowUp Pressed: Current Percent=${currentPercent}, Step=${stepPercent}, New Percent=${newPercent}`);
    } else if (key === 'ArrowDown') {
        newPercent = Math.min(currentPercent + stepPercent, 100);
        console.log(`ArrowDown Pressed: Current Percent=${currentPercent}, Step=${stepPercent}, New Percent=${newPercent}`);
    }

    paddle1.style.top = `${newPercent}%`; // Update the DOM using percentages
    return newPercent;  // Send this to the server
}

document.addEventListener('keydown', throttle(function(event) {
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        const newPosition = getPaddlePosition(event.key);
        console.log("Sending new position to server: ", newPosition);
        gameSocket.send(JSON.stringify({
            action: 'move_paddle',
            position: newPosition,
            user_id: 1  // Ensure the user ID is correctly managed
        }));
    }
}, 50));


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
