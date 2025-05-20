// Variables globales
let datos = []; // Almacena los datos históricos
let graficoOil, graficoWater, graficoBSW, graficoAccumulatedOil; // Objetos de gráficos
let datosHistoricos = [];
let fechasHistoricas = [];
let simulacionValidacion = {};
let simulacionFuturo = {};

/* Función: inicializarGraficos
 * Desc: Crea y configura los gráficos iniciales
 */
function inicializarGraficos() {
  // Configuración común para todos los gráficos
  const configComun = {
    type: 'line',
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        zoom: {
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'x'
          },
          pan: {
            enabled: true,
            mode: 'x'
          },
          limits: {
            x: { min: 'original', max: 'original' },
            y: { min: 'original', max: 'original' }
          }
        },
        title: {
          display: true,
          font: { size: 16 }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Tiempo',
            font: { weight: 'bold' }
          }
        },
        y: {
          title: {
            display: true,
            text: 'Valor',
            font: { weight: 'bold' }
          }
        }
      }
    }
  };

  // Crear gráfico de petróleo
  graficoOil = new Chart(document.getElementById('graficoOil'), {
    ...configComun,
    data: {
      labels: [],
      datasets: [{
        label: 'Rate Oil (observado)', 
        borderColor: '#FF6384', // Rojo
        backgroundColor: '#FF638433',
        fill: false
        
      }, 
      {
        label: 'Rate Oil (simulado)',
        borderColor: '#36A2EB', // Azul
        backgroundColor: '#36A2EB33',
        fill: false
      }]
    },
    options: {
      ...configComun.options,
      plugins: { 
        ...configComun.plugins,
        title: { text: 'Tasa de Petróleo' }
      }
    }
  });

  // Gráfico de agua 
  graficoWater = new Chart(document.getElementById('graficoWater'), {
    ...configComun,
    data: {
      labels: [],
      datasets: [{
        label: 'Rate Water (observado)',
        borderColor: '#4BC0C0', // Turquesa
        backgroundColor: '#4BC0C033',
        fill: false
      }, {
        label: 'Rate Water (acumulado)',
        borderColor: '#FFCE56', // Amarillo
        backgroundColor: '#FFCE5633',
        fill: false
      }]
    },
    options: {
      ...configComun.options,
      plugins: { title: { text: 'Tasa de Agua' } }
    }
  });

  // Gráfico de BSW 
  graficoBSW = new Chart(document.getElementById('graficoBSW'), {
    ...configComun,
    data: {
      labels: [],
      datasets: [{
        label: 'BSW % (observado)',
        borderColor: '#9966FF', // Morado
        backgroundColor: '#9966FF33',
        fill: false
      }, {
        label: 'BSW % (acummulado)',
        borderColor: '#4A4A4A', // Gris
        backgroundColor: '#4A4A4A33',
        fill: false
      }]
    },
    options: {
      ...configComun.options,
      plugins: { title: { text: 'BSW (%)' } }
    }
  });

  graficoAccumulatedOil = new Chart(document.getElementById('graficoAccumulatedOil'), {
    ...configComun,
    data: {
      label: [],
      datasets:[
        {
          label: 'Producción acumulada',
          borderColor: '#9966FF', // Morado
          backgroundColor: '#9966FF33',
          fill: false
        },
        {
          label: 'Histórico producción',
          borderColor: '#c65353', 
          backgroundColor: '#9966FF33',
          fill: false
        },
      ]
    },
    options: {
      ...configComun.options,
      plugins: { title: { text: 'Producción acumulada' } }
    }
  })
}

/* Función: iniciarAjuste
 * Desc: Función principal que coordina el proceso de ajuste
 */
function iniciarAjuste(){
  if (datos.length === 0) {
    alert('Primero cargue un archivo CSV válido');
    return;
  }

  // Generar datos simulados
  const tiempo = datos.map(d => d.Tiempo);
  const oilObs = datos.map(d => d.RateOil);
  const waterObs = datos.map(d => d.RateWater);
  const bswObs = datos.map(d => d.BSW);

  // Simulación básica con variación aleatoria
  const oilSim = oilObs.map(v => v * 0.95 + Math.random() * 10);
  const waterSim = waterObs.map(v => v * 1.05 + Math.random() * 5);
  const bswSim = bswObs.map(v => v + (Math.random() * 2 - 1));

  // Actualizar gráficos
  actualizarGrafico(graficoOil, tiempo, oilObs, oilSim);
  actualizarGrafico(graficoWater, tiempo, waterObs, waterSim);
  actualizarGrafico(graficoBSW, tiempo, bswObs, bswSim);

  // Calcular y mostrar errores
  mostrarErrores({
    oil: calcularECM(oilObs, oilSim),
    water: calcularECM(waterObs, waterSim),
    bsw: calcularECM(bswObs, bswSim)
  });
  graficarDeclinacionArps(tiempo, oilObs);

}

/* Función: actualizarGrafico
 * Parámetros:
 *   - grafico: Objeto Chart.js
 *   - labels: Array de etiquetas de tiempo
 *   - obs: Datos observados
 *   - sim: Datos simulados
 * Desc: Actualiza un gráfico con nuevos datos
 */
function actualizarGrafico(grafico, labels, obs, sim) {
  grafico.data.labels = labels;
  grafico.data.datasets[0].data = obs;
  grafico.data.datasets[1].data = sim;
  grafico.update();
}

/* Función: calcularECM
 * Parámetros:
 *   - obs: Array de valores observados
 *   - sim: Array de valores simulados
 * Retorna: Error Cuadrático Medio
 */
function calcularECM(obs, sim) {
  return obs.reduce((acc, val, i) => acc + Math.pow(val - sim[i], 2), 0) / obs.length;
}

/* Función: mostrarErrores
 * Parámetros:
 *   - errores: Objeto con valores de error
 * Desc: Muestra los errores en la interfaz
 */
function mostrarErrores(errores) 

{
  document.getElementById('resultados').innerHTML = `
    <h3 style="color: #1b4965;">Métricas de Error</h3>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1em;">
      <div style="color: #FF6384;">
        <strong>Petróleo</strong><br>
        ECM: ${errores.oil.toFixed(2)}
      </div>
      <div style="color: #4BC0C0;">
        <strong>Agua</strong><br>
        ECM: ${errores.water.toFixed(2)}
      </div>
      <div style="color: #9966FF;">
        <strong>BSW</strong><br>
        ECM: ${errores.bsw.toFixed(2)}
      </div>
    </div>
  `;
}


// Evento: Carga de archivo CSV
document.getElementById('csvInput').addEventListener('change', async function(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("archivo", file);

  const response = await fetch('/procesar', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    alert("Error al procesar el archivo");
    return;
  }

  const result = await response.json();

  // Guardamos datos globales
  datosHistoricos = result.historico.valores;
  fechasHistoricas = result.historico.fechas;
  accumulatedOil = result.historico.accumulatedOil;

  accumulatedWater = result.historico.accumulatedWater;
  rateWater = result.historico.rateWater;

  bsw = result.historico.bsw;
  accumulatedBSW = result.historico.accumulatedBSW
  
  simulacionValidacion = result.validacion;
  simulacionFuturo = result.futuro;



  // Mostrar solo el histórico inicialmente
  graficoOil.data.labels = fechasHistoricas;
  graficoOil.data.datasets[0].data = datosHistoricos;
  graficoOil.data.datasets[1].data = []; // simulaciones limpias
  graficoOil.update();

  //gráfico acumulado CRUDO
  graficoAccumulatedOil.data.labels = fechasHistoricas 
  graficoAccumulatedOil.data.datasets[0].data = accumulatedOil
  graficoAccumulatedOil.data.datasets[1].data = datosHistoricos
  graficoAccumulatedOil.update()

  //gráfico agua
  graficoWater.data.labels = fechasHistoricas
  graficoWater.data.datasets[0].data = rateWater
  graficoWater.data.datasets[1].data = accumulatedWater
  graficoWater.update()

  //grafico bsw
  graficoBSW.data.labels = fechasHistoricas
  graficoBSW.data.datasets[0].data = bsw
  graficoBSW.data.datasets[1].data = accumulatedBSW
  graficoBSW.update()

});


/*function ejecutarSimulaciones() {
  if (!simulacionFuturo || !simulacionFuturo.fechas) {
    alert("Primero carga un archivo válido.");
    return;
  }

  const fechasCompletas = fechasHistoricas.concat(simulacionFuturo.fechas);
  const padding = new Array(simulacionFuturo.fechas.length).fill(null);

  const obsConPadding = datosHistoricos.concat(padding);
  const p10 = new Array(fechasHistoricas.length).fill(null).concat(simulacionFuturo.p10);
  const p50 = new Array(fechasHistoricas.length).fill(null).concat(simulacionFuturo.p50);
  const p90 = new Array(fechasHistoricas.length).fill(null).concat(simulacionFuturo.p90);

  graficoOil.data.labels = fechasCompletas;
  graficoOil.data.datasets = [
    {
      label: 'Histórico',
      data: obsConPadding,
      borderColor: '#FF6384',
      fill: false
    },
    {
      label: 'P10',
      data: p10,
      borderColor: '#0077b6',
      borderDash: [5, 5],
      fill: false
    },
    {
      label: 'P50',
      data: p50,
      borderColor: '#2a9d8f',
      fill: false
    },
    {
      label: 'P90',
      data: p90,
      borderColor: '#8338ec',
      borderDash: [5, 5],
      fill: false
    }
  ];

  graficoOil.update();
}*/


function ejecutarSimulaciones() {
  if (!simulacionFuturo || !simulacionFuturo.fechas) {
    alert("Primero carga un archivo válido.");
    return;
  }

  const fechasFuturas = simulacionFuturo.fechas;
  const todasSim = simulacionFuturo.simulaciones;

  const fechasCompletas = fechasHistoricas.concat(fechasFuturas);
  const padding = new Array(fechasHistoricas.length).fill(null);

  // Preparar datasets: primero histórico
  const datasets = [{
    label: 'Histórico',
    data: datosHistoricos.concat(new Array(fechasFuturas.length).fill(null)),
    borderColor: '#FF6384',
    backgroundColor: '#FF638433',
    borderWidth: 2,
    fill: false,
    order: 5
  }];

  // Agregar simulaciones con opacidad baja
  /*todasSim.forEach(sim => {
    datasets.push({
      label: 'Simulación',
      data: padding.concat(sim),
      borderColor: 'rgba(249, 231, 231, 0.1)',
      backgroundColor: 'rgba(147, 136, 136, 0.05)',
      borderWidth: 1,
      fill: false,
      pointRadius: 0,
      order: 1
    });
  });*/

  // Agregar percentiles
  const p10 = padding.concat(simulacionFuturo.p10);
  const p50 = padding.concat(simulacionFuturo.p50);
  const p90 = padding.concat(simulacionFuturo.p90);

   datasets.push(
    {
      label: 'P10',
      data: padding.concat(simulacionFuturo.p10),
      borderColor: '#0077b6',
      borderDash: [5, 5],
      borderWidth: 2,
      fill: false,
      order: 10
    },
    {
      label: 'P50',
      data: padding.concat(simulacionFuturo.p50),
      borderColor: '#2a9d8f',
      borderWidth: 2,
      fill: false,
      order: 11
    },
    {
      label: 'P90',
      data: padding.concat(simulacionFuturo.p90),
      borderColor: '#8338ec',
      borderDash: [5, 5],
      borderWidth: 2,
      fill: false,
      order: 12
    }
  );

  graficoOil.data.labels = fechasCompletas;
  graficoOil.data.datasets = datasets;
  graficoOil.update();
}



/* Función: graficarDeclinacionArps
 * Desc: Agrega una gráfica con el modelo de declinación exponencial de Arps
 */
 function graficarDeclinacionArps(tiempo, rateOilObs) {
  // Encontrar primer valor válido
  const qi = rateOilObs.find(v => typeof v === 'number' && !isNaN(v)) || 1000;
  const D = 0.01; // tasa de declinación

  const qt = rateOilObs.map((_, i) => +(qi * Math.exp(-D * i)).toFixed(2));

  const ctx = document.getElementById('graficoDeclinacion').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: tiempo,
      datasets: [
        {
          label: 'RateOil observado',
          data: rateOilObs,
          borderColor: '#FF6384',
          backgroundColor: '#FF638433',
          fill: false
        },
        {
          label: 'Arps Exponencial (simulado)',
          data: qt,
          borderColor: '#00b894',
          backgroundColor: '#00b89433',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Comparación: Producción Observada vs. Arps Exponencial',
          font: { size: 16 }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Tiempo',
            font: { weight: 'bold' }
          }
        },
        y: {
          title: {
            display: true,
            text: 'Producción (RateOil)',
            font: { weight: 'bold' }
          }
        }
      }
    }
  });
}


// Inicialización al cargar la página
window.onload = inicializarGraficos;