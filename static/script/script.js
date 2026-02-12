function book() {
    // Get form values
    const name = document.getElementById("name").value;
    const phone = document.getElementById("phone").value;
    const date = document.getElementById("date").value;
    const time = document.getElementById("time").value;

    fetch("/book", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name, phone, date, time })
    })
    .then(res => res.json().then(data => ({status: res.status, body: data})))
    .then(obj => {
        // Show response message
        const msg = document.getElementById("message");
        msg.innerText = obj.body.message;

        // Optional: clear form on success
        if (obj.status === 200) {
            document.getElementById("name").value = "";
            document.getElementById("phone").value = "";
            document.getElementById("date").value = "";
            document.getElementById("time").value = "";
        }
    })
    .catch(err => {
        console.error(err);
        document.getElementById("message").innerText = "Error, try again.";
    });
}
