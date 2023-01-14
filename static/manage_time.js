var button = document.getElementById("submit");
button.addEventListener("click", function() {
  var data = {};
  var rows = document.querySelectorAll("#table tr");
  rows.forEach(row => {
      var row_name = row.id;
      var cols = row.querySelectorAll("td");
      data[row_name] = [];
      cols.forEach(col => {
          data[row_name].push(col.innerHTML);
      })});

  fetch("/manage_time_back", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data),
    redirect: "follow"
  })
  .then(function(response) {
    return response.text();
  })
  .then(response => {
    window.location.href = "/msg?msg=表單已儲存！"
  });
});

let trIdCounter = 0;
const addButton = document.getElementById("add");
const table = document.getElementById("table");

addButton.addEventListener("click", function() {
  var newRow = table.insertRow(-1);
  newRow.id = `tr-${trIdCounter}`
  for (var i = 0; i < 4; i++) {
      var newCell = newRow.insertCell(i);
      if(i == 1) {
        newCell.innerHTML = "available";
      }
      newCell.contentEditable = true;
  }
  trIdCounter++;
});



