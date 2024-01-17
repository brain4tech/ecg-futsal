// Declare variables for DOM elements
let start = document.querySelector("#start");
let submit = document.querySelector("#submit");
let scoreButtons = document.querySelectorAll('.scorebtn');
let homeScore = document.querySelector("#homeScore");
let awayScore = document.querySelector("#awayScore");

// Add eventlisteners
start.addEventListener("click", startMatch);

// My functions
function startMatch() {
  // Activate score buttons
  scoreButtons.forEach(function(element) {
    element.addEventListener('click', adjustScore)
  });

  // Hide start button, show submit button
  start.classList.toggle("d-none");
  submit.classList.toggle("d-none");

  // Set counter
  var gameTime = parseInt(document.getElementById("minutes").innerText);
  var timerDistance = gameTime * 60 * 1000;

  // Update the count down every 1 second
  var x = setInterval(function() {

    // Decrease distance by 1 second

    timerDistance = timerDistance - 1000;

    // Time calculations for minutes and seconds
    var minutes = Math.floor((timerDistance % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2, '0');
    var seconds = Math.floor((timerDistance % (1000 * 60)) / 1000).toString().padStart(2, '0');

    // Output the result in an element with id="demo"
    document.getElementById("minutes").innerHTML = minutes;
    document.getElementById("seconds").innerHTML = seconds;

    // If the count down is over, write some text
    if (timerDistance < 0) {
      clearInterval(x);
      document.getElementById("minutes").innerHTML = "00";
      document.getElementById("seconds").innerHTML = "00";
    }
  }, 1000);
}


function adjustScore(event) {
  home = parseInt(homeScore.innerHTML)
  away = parseInt(awayScore.innerHTML)

  switch(event.target.id) {
    case "addHome":
      home++
      break;
    case "addAway":
      away++
      break;
    case "minHome":
      home = Math.max(home - 1, 0)
      break;
    case "minAway":
      away = Math.max(away - 1, 0)
      break;
    default:
      break;
  }
  homeScore.innerHTML = home;
  awayScore.innerHTML = away;
  document.getElementById("homeScoreSubmit").value = home
  document.getElementById("awayScoreSubmit").value = away
}

