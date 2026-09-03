let playAgain = true;

while (playAgain) {
    let ranNum = Math.floor(Math.random() * 11); //1-10//
    
    while (true) {
        let userNum = Number(prompt("Guess a number between 0 and 10"));
        if (userNum == ranNum) {
            alert("Yeah, you guessed it!");
            break;
        } else if (userNum > ranNum) {
            alert("Too high, try again");
        } else {
            alert("Too low, try again");
        }
    }
    playAgain = confirm("Do you want to play again?");
}
alert("Thanks for playing!");