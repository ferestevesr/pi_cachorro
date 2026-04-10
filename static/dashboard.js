function carregarAlertas(){
    fetch("/alertas")
      .then(res => res.json())
      .then(data => {
        console.log(data);
      });
  }