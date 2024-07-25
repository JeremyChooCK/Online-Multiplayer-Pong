const gameSocket = new WebSocket('wss://localhost/ws/game/');
const paddle1 = document.getElementById('paddle1');
const paddle2 = document.getElementById('paddle2');
const ball = document.getElementById('ball');
const player1Score = document.getElementById('player1Score');
const player2Score = document.getElementById('player2Score');
const startButton = document.getElementById('startButton');

gameSocket.onmessage = function(event) {
    console.log("Message received: ", event.data);
    const data = JSON.parse(event.data);
    ball.style.left = `${data.ball_position.x}%`;
    ball.style.top = `${data.ball_position.y}%`;
    paddle1.style.top = `${data.paddle_positions.player1}%`;
    paddle2.style.top = `${data.paddle_positions.player2}%`;
    // Update scores
    player1Score.textContent = data.score.player1;
    player2Score.textContent = data.score.player2;
};

gameSocket.onopen = function() {
    startButton.addEventListener('click', function() {
        gameSocket.send(JSON.stringify({
            'action': 'start_game'
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
            user_id: 'player1'  // Ensure this is correctly identified
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
