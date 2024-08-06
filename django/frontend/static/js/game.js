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
        }
        if (data.paddle_positions.player2 !== undefined) {
            paddle2.style.top = `${data.paddle_positions.player2}%`;
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

document.addEventListener('keydown', function(event) {
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        const newPosition = getPaddlePosition(event.key);
        console.log("Sending new position: ", newPosition);
        gameSocket.send(JSON.stringify({
            action: 'move_paddle',
            position: newPosition,
            user_id: 1  // Use a numeric value for user_id
        }));
    }
});

function getPaddlePosition(key) {
    const currentTop = parseInt(window.getComputedStyle(paddle1).getPropertyValue("top"));
    if (key === 'ArrowUp') {
        return Math.max(currentTop - 20, 0);  // Move up by reducing the top value
    } else if (key === 'ArrowDown') {
        return Math.min(currentTop + 20, document.getElementById('pongGame').offsetHeight - paddle1.offsetHeight);  // Move down by increasing the top value
    }
}

gameSocket.onclose = function(event) {
    console.log('WebSocket closed. If the game is over, redirect or handle post-game actions.');
    // Optionally, redirect to a different page or display any relevant UI element
};
