const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = 400;
canvas.height = 400;

const box = 20;
let snake = [{ x: 200, y: 200 }];
let direction = "RIGHT";
let food = {
    x: Math.floor(Math.random() * (canvas.width / box)) * box,
    y: Math.floor(Math.random() * (canvas.height / box)) * box
};

let game;  // Store interval reference
let gameOver = false;

// Move the snake
function moveSnake() {
    let head = { ...snake[0] };

    if (direction === "UP") head.y -= box;
    if (direction === "DOWN") head.y += box;
    if (direction === "LEFT") head.x -= box;
    if (direction === "RIGHT") head.x += box;

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
        food = {
            x: Math.floor(Math.random() * (canvas.width / box)) * box,
            y: Math.floor(Math.random() * (canvas.height / box)) * box
        };
    } else {
        snake.pop();
    }
}

// Draw Snake & Food
function draw() {
    ctx.fillStyle = "#FBF5E5";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#A35C7A";
    snake.forEach((segment) => {
        ctx.fillRect(segment.x, segment.y, box, box);
    });

    ctx.fillStyle = "#C890A7";
    ctx.fillRect(food.x, food.y, box, box);
}

// **Game Loop**
function update() {
    if (gameOver) return;

    moveSnake();

    // **Check if the snake hits the wall**
    let head = snake[0];
    if (head.x < 0 || head.x >= canvas.width || head.y < 0 || head.y >= canvas.height) {
        gameOver = true;
        showGameOverScreen();
        return;
    }

    draw();
}

// **Show "Press any key to replay" message**
function showGameOverScreen() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "white";
    ctx.font = "24px Arial";
    ctx.textAlign = "center";
    ctx.fillText("Game Over!", canvas.width / 2, canvas.height / 2 - 20);
    ctx.fillText("Press any key to replay", canvas.width / 2, canvas.height / 2 + 20);

    document.addEventListener("keydown", restartGame, { once: true });
}

// **Restart Game**
function restartGame() {
    gameOver = false;
    snake = [{ x: 200, y: 200 }];
    direction = "RIGHT";
    clearInterval(game);  // ✅ Prevent multiple intervals
    startGame();
}

// **Start the Game**
function startGame() {
    clearInterval(game);
    game = setInterval(update, 100);
}

// **Start the game initially**
startGame();

// Change Direction
document.addEventListener("keydown", (event) => {
    if (event.key === "ArrowUp" && direction !== "DOWN") direction = "UP";
    if (event.key === "ArrowDown" && direction !== "UP") direction = "DOWN";
    if (event.key === "ArrowLeft" && direction !== "RIGHT") direction = "LEFT";
    if (event.key === "ArrowRight" && direction !== "LEFT") direction = "RIGHT";
});
