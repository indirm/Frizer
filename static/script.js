function book() {
    fetch("/book", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: document.getElementById("name").value,
            phone: document.getElementById("phone").value,
            date: document.getElementById("date").value,
            time: document.getElementById("time").value
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("message").innerText = "Appointment booked!";
    });
}
