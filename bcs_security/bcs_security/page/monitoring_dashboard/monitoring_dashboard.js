frappe.pages['monitoring-dashboard'].on_page_load = function(wrapper) {

    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Monitoring Dashboard',
        single_column: true
    });

    frappe.require([
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"
    ], function () {

        let currentChart = null;
        let current_metric = "cpu";

        let html = `
        <div>

            <h4>Select Host</h4>
            <select id="hostSelect" class="form-control mb-3"></select>

            <div class="row mb-3">
                <div class="col-md-4">
                    <label>From</label>
                    <input type="datetime-local" id="fromDate" class="form-control">
                </div>
                <div class="col-md-4">
                    <label>To</label>
                    <input type="datetime-local" id="toDate" class="form-control">
                </div>
                <div class="col-md-4 mt-4">
                    <button class="btn btn-primary" id="applyFilter">Apply</button>
                </div>
            </div>

            <div class="mb-3">
                <button class="btn btn-light quick" data-min="5">Last 5 min</button>
                <button class="btn btn-light quick" data-min="60">Last 1 hour</button>
                <button class="btn btn-light quick" data-min="1440">Last 1 day</button>
            </div>

            <div class="btn-group mb-3">
                <button class="btn btn-default metric" data-type="cpu">CPU</button>
                <button class="btn btn-default metric" data-type="disk">Disk</button>
                <button class="btn btn-default metric" data-type="memory">Memory</button>
                <button class="btn btn-default metric" data-type="network">Network</button>
                <button class="btn btn-default metric" data-type="uptime">Uptime</button>
            </div>

            <canvas id="chart" height="100"></canvas>

        </div>
        `;

        $(html).appendTo(page.body);

        // Load hosts
        frappe.call({
            method: "bcs_security.api.dashboard.get_hosts",
            callback: function(r) {

                let select = $("#hostSelect");

                r.message.forEach(host => {
                    select.append(
                        `<option value="${host.zabbix_host_id}" data-server="${host.custom_zabbix_server}">
                            ${host.custom_virtual_machine || host.name}
                        </option>`
                    );
                });

                setTimeout(loadChart, 500);
            }
        });

        // Events
        $(document).on("change", "#hostSelect", loadChart);
        $("#applyFilter").on("click", loadChart);

        $(document).on("click", ".metric", function() {
            current_metric = $(this).data("type");
            loadChart();
        });

        $(document).on("click", ".quick", function() {

            let minutes = $(this).data("min");

            let now = new Date();
            let past = new Date(now.getTime() - minutes * 60000);

            $("#toDate").val(formatDate(now));
            $("#fromDate").val(formatDate(past));

            loadChart();
        });

        function formatDate(date) {
            return date.toISOString().slice(0,16);
        }

        // Load chart
        function loadChart() {

            let host_id = $("#hostSelect").val();
            let server = $("#hostSelect option:selected").data("server");

            if (!host_id || !server) {
                console.log("Missing host/server", host_id, server);
                return;
            }

            frappe.call({
                method: "bcs_security.api.dashboard.get_metric_data",
                args: {
                    host_id: host_id,
                    zabbix_server: server,
                    metric_type: current_metric,
                    from_date: $("#fromDate").val(),
                    to_date: $("#toDate").val()
                },
                callback: function(r) {

                    if (!r.message || r.message.values.length === 0) {
                        frappe.msgprint("No data available");
                        return;
                    }

                    let ctx = document.getElementById("chart");

                    if (currentChart) currentChart.destroy();

                    let values = r.message.values;

                    // convert uptime to hours
                    if (current_metric === "uptime") {
                        values = values.map(v => (v / 3600).toFixed(2));
                    }

                    currentChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: r.message.labels,
                            datasets: [{
                                label: current_metric === "uptime" ? "UPTIME (hours)" : current_metric.toUpperCase(),
                                data: values,
                                tension: 0.3
                            }]
                        }
                    });
                }
            });
        }

    });
};