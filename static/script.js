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
    function book() {
    fetch("/book", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        date: document.getElementById("date").value,
        time: document.getElementById("time").value
    })
})
.then(res => res.json().then(data => ({status: res.status, body: data})))
.then(obj => {
    document.getElementById("message").innerText = obj.body.message;
})
.catch(err => {
    console.error(err);
    document.getElementById("message").innerText = "Error, try again.";
});

}
}