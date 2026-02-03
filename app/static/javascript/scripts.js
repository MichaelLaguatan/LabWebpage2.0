window.addEventListener("load", async () => {
  try {
    const response = await fetch("/api/power_states");

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const powerData = await response.json();
      for (const [ip, state] of Object.entries(powerData)) {
        const el = document.getElementById(ip);
        if (!el) continue;
        el.style.backgroundColor = 
              state === "On"  ? "green" :
              state === "Off" ? "#C20707" :
              "";
      }
  } catch (err) {
    console.error("Failed to fetch power states:", err);
  }
});

/* MODAL STUFF */

var infoModal = document.getElementById("infoModal");
var closeButton = document.getElementsByClassName("close")[0];
var titleText = document.getElementById("titleText");
var oobmText = document.getElementById("oobmText");
var managementText = document.getElementById("managementText");
var serial = document.getElementById("serial");
var productModel = document.getElementById("product");
var login = document.getElementById("login");

window.showModal = async function (server_name) {
  const res = await fetch(`api/modal/?server_name=${encodeURIComponent(server_name)}`);
  const server = await res.json();
  titleText.innerHTML = server.name;
  oobmText.innerHTML = server.oobm;
  managementText.innerHTML = server.mgmt;
  serial.innerHTML = server.serial_number;
  productModel.innerHTML = server.product_number;
  login.innerHTML = server.login;

  infoModal.style.display = "block";
}

function hideModal() {
  infoModal.style.display = "none";
}

closeButton.onclick = hideModal;

window.onclick = function (event) {
  if (event.target == infoModal) {
    infoModal.style.display = "none";
  }
};

/* SERVER STUFF */

window.powerOn = function powerOn(serverName, ip) {
  var req = new XMLHttpRequest();
  var url = `/api/power_on/${ip}?server_name=${encodeURIComponent(serverName)}`;
  req.open("POST",url,true);
  req.send();

  var powerBox = document.getElementById(ip);
  powerBox.innerHTML = '<img src="static/images/loading.gif" class="powerButton">';
  req.onreadystatechange = function() {
    if (req.readyState === 4) {
      powerBox.innerHTML = '<input type="image" src="static/images/poweron.png" class="powerButton" onclick="powerOn(\''+ip+'\')"/>';
      console.log(req.response);
      if (req.status == 204 || req.status == 200) {
        alert("Successfully powered on " + ip);
        powerBox.style.backgroundColor = 'green';
      } else if (req.status == 409) {
        alert(ip + " is already powered on");
        powerBox.style.backgroundColor = 'green';
      } else {
        alert('Failed to power on. Check if server is already powered on ' + ip);
      }
    }
  }
}