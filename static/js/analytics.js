//charts + customize

new Chart(document.getElementById("killsChart"), {
    type: "bar",
    data: {
        labels: killerLabels,
        datasets: [{
            label: "Kills",
            data: killerData,
            backgroundColor: "rgb(231, 162, 58)",
            borderWidth: 2
        }]
    }
});

new Chart(document.getElementById("championChart"), {
    type: "doughnut",
    data: {
        labels: championLabels,
        datasets: [{
            data: championData
        }]
    }
});

//green if win rate is >40, red if <50
const colors = teamData.map(rate =>
    rate >= 50 ? "#2ecc71" : "#e74c3c"
);

new Chart(document.getElementById("teamChart"), {
    type: "bar",
    data: {
        labels: teamLabels,
        datasets: [{
            label: "Win Rate (%)",
            data: teamData,
            backgroundColor: colors,
            borderColor: colors,
            borderWidth: 2
        }]
    }
});