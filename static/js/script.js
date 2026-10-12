 // Agregamos la palabra 'async' porque el mensajero tomará un par de segundos en ir y volver
        async function lanzarCalculo() {
            const cliente = document.getElementById("cliente").value;
            const distancia = document.getElementById("distancia").value;
            const invertir = document.getElementById("invertir").checked;

            if(!cliente || !distancia) {
                alert("⚠️ Error: El sistema requiere el ID del cliente y la distancia en metros para operar.");
                return;
            }

            const url = `/generar_kml?cliente=${cliente}&distancia_otdr=${distancia}&invertir=${invertir}`;
            
            try {
                // EL HACK: Enviamos al mensajero invisible (fetch) a hablar con Python
                const respuesta = await fetch(url);
                
                // Revisamos la etiqueta del paquete que nos devolvió Python
                const tipoContenido = respuesta.headers.get("content-type");
                
                // Si la etiqueta dice JSON, significa que Python nos mandó un error
                if (tipoContenido && tipoContenido.includes("application/json")) {
                    const datos = await respuesta.json(); // Abrimos el texto
                    alert(datos.error); // 🚨 AQUÍ mostramos el mensaje flotante de error
                } 
                // Si no es JSON, significa que es nuestro archivo KML
                else {
                    const blob = await respuesta.blob(); // Convertimos la respuesta en un archivo físico
                    
                    // Creamos un botón de descarga invisible, lo presionamos automáticamente y lo borramos
                    const enlaceDescarga = document.createElement("a");
                    enlaceDescarga.href = window.URL.createObjectURL(blob);
                    enlaceDescarga.download = `Falla_${cliente}.kml`;
                    document.body.appendChild(enlaceDescarga);
                    enlaceDescarga.click();
                    enlaceDescarga.remove();
                }
            } catch (error) {
                alert("⚠️ No se pudo conectar con el servidor. Revisa si Uvicorn está encendido.");
            }
        }