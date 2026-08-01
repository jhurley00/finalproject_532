new Chart(document.getElementById("regionChart"), {
    type: "doughnut",

    data: {
        labels: regionLabels,

        datasets: [{
            data: regionData,

            backgroundColor: [
                "#f11a1a",
                "#2337eb",
                "#0d5e06",
                "#442878",
                "#dd4e15",
                "#A09B8C",
                "#1E2328"
            ],

            borderColor: "#ffffff",
            borderWidth: 2
        }]
    },

    options: {
        responsive: true,

        plugins: {
            legend: {
                position: "bottom"
            }
        }
    }
});