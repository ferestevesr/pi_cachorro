let map;

function initMap(lat, lng) {
  const local = { lat: lat, lng: lng };

  map = new google.maps.Map(document.getElementById("map"), {
    center: local,
    zoom: 14,
  });

  new google.maps.Marker({
    position: local,
    map: map,
  });
}

function buscarDelegacias() {
  const endereco = document.getElementById("endereco").value;

  const geocoder = new google.maps.Geocoder();

  geocoder.geocode({ address: endereco }, (results, status) => {
    if (status === "OK") {
      const location = results[0].geometry.location;
      initMap(location.lat(), location.lng());
    } else {
      alert("Endereço não encontrado");
    }
  });
}