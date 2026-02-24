console.log("JS activo");
alert("JS FUNCIONANDO");

document.addEventListener("DOMContentLoaded", function () {

    const depSelect = document.getElementById("departamento");
    const provSelect = document.getElementById("provincia");
    const zona = document.querySelector("select[name='ZonaInspeccion']");
    const tbody = document.getElementById("tabla-body");

    // ===========================
    // Función para actualizar la zona
    // ===========================
    function actualizarZona() {
        const dep = depSelect.value;
        const prov = provSelect.value;

        if (!dep || !prov) {
            zona.value = "";
            return;
        }

        // SOLO aplica regla si no hay valor guardado
        if (!zona.value) {
            zona.value = (dep === "15" && prov === "01") ? "L" : "P";
        }
    }

    // ===========================
    // Cargar provincias dinámicamente
    // ===========================
    function cargarProvincias(dep, provSeleccionada = null) {
        provSelect.innerHTML = `<option value="">Seleccione Provincia</option>`;
        tbody.innerHTML = ""; // limpiar tabla

        if (!dep) return;

        fetch(`/ajax/provincias/?dep=${dep}`)
            .then(r => r.json())
            .then(data => {
                data.forEach(p => {
                    const opt = document.createElement("option");
                    opt.value = p.CodigoProvincia;
                    opt.textContent = p.Nombre;
                    provSelect.appendChild(opt);
                });

                // Selecciona la provincia guardada si existe
                if (provSeleccionada) provSelect.value = provSeleccionada;

                // Actualiza zona después de seleccionar provincia
                actualizarZona();
            });
    }

    // ===========================
    // Cargar ubicaciones dinámicamente
    // ===========================
    function cargarUbicaciones(dep, prov) {
        tbody.innerHTML = "";
        if (!dep || !prov) return;

        fetch(`/ajax/ubicaciones/?dep=${dep}&prov=${prov}`)
            .then(res => res.json())
            .then(data => {
                data.forEach((u, i) => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${i + 1}</td>
                        <td>${u.CodigoInterno}</td>
                        <td>
                            ${u.CodigoUbicacion}
                            <input type="hidden" name="codigo_ubicacion[]" value="${u.CodigoUbicacion}">
                            <input type="hidden" name="codigo_provincia[]" value="${u.CodigoProvincia}">
                            <input type="hidden" name="codigo_distrito[]" value="${u.CodigoDistrito}">
                        </td>
                        <td>${u.DireccionComercial}</td>
                        <td>${u.CodigoProvincia}</td>
                        <td>${u.CodigoDistrito}</td>
                        <td>${u.CodigoTipoElemento}</td>
                        <td>${u.Medidas}</td>
                        <td>
                            <select name="estado_elemento[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="01">Encendido</option>
                                <option value="02">Apagado</option>
                            </select>
                        </td>
                        <td>
                            <select name="punto_luz[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="1">SI</option>
                                <option value="0">NO</option>
                            </select>
                        </td>
                        <td>
                            <input type="number" name="num_reflectores[]" class="form-control form-control-sm">
                        </td>
                        <td>
                            <select name="estado_reflectores[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="01">Encendidos</option>
                                <option value="02">Apagados</option>
                            </select>
                        </td>
                        <td>
                            <select name="publicidad_lona[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="1">SI</option>
                                <option value="0">NO</option>
                            </select>
                        </td>
                        <td>
                            <select name="control_publicidad[]" class="form-select form-select-sm">
                                <option value="">—</option>
                                <option value="01">OK – No requiere acción</option>
                                <option value="02">Renovar contrato</option>
                                <option value="03">Programar retiro</option>
                                <option value="04">Programar cambio de lona</option>
                                <option value="05">Enviar a mantenimiento</option>
                                <option value="06">Retiro urgente</option>
                                <option value="07">Bloquear facturación</option>
                                <option value="08">Liberar panel para venta</option>
                            </select>
                        </td>
                        <td>
                            <select name="estado_lona[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="01">En exhibición</option>
                                <option value="02">Vencido</option>
                                <option value="03">Reservado para cambio</option>
                                <option value="04">En observación</option>
                                <option value="05">Dañado</option>
                                <option value="06">En retiro</option>
                                <option value="07">Fuera de contrato</option>
                                <option value="08">Suspendido temporalmente</option>
                            </select>
                        </td>
                        <td>
                            <select name="estado_logo[]" class="form-select form-select-sm">
                                <option value="">Seleccione</option>
                                <option value="01">TIENE</option>
                                <option value="02">NO TIENE</option>
                            </select>
                        </td>
                        <td>
                            <input type="text" name="observaciones[]" class="form-control form-control-sm">
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // ===========================
    // Eventos de cambio
    // ===========================
    depSelect.addEventListener("change", function () {
        cargarProvincias(this.value, null);
        tbody.innerHTML = "";
    });

    provSelect.addEventListener("change", function () {
        cargarUbicaciones(depSelect.value, provSelect.value);
        actualizarZona();
    });

    // ===========================
    // Inicialización en modo modificación
    // ===========================
    if (depSelect.value) {
        const provGuardada = provSelect.getAttribute("data-selected") || provSelect.value;
        cargarProvincias(depSelect.value, provGuardada);
    }

});