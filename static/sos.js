function ativarSOS() {
    const status = document.getElementById("status");
  
    navigator.geolocation.getCurrentPosition(function(pos){
  
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      const localizacao = lat + "," + lng;
  
      fetch("/alerta", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          localizacao: localizacao,
          mensagem: "SOS ativado"
        })
      })
      .then(res => res.json())
      .then(data => {
        status.innerText = "🔴 SOS enviado!";
        document.body.classList.add("alerta");
  
        // opcional: mostrar no mapa também
        initMap(lat, lng);
      });
  
    }, function(){
      alert("Erro ao pegar localização");
    });
  }