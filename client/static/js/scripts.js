let backendUrl = '';

async function fetchNgrokUrl() {
    try {
        const response = await fetch('/backend_url');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        backendUrl = data.backend_url;
        console.log('Fetched backend URL:', backendUrl); // Debugging statement
    } catch (error) {
        console.error('Error fetching backend URL:', error);
    }
}

async function submitForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    data.include_battery = document.getElementById('include_battery').checked;
    data.include_solar = document.getElementById('include_solar').checked;
    data.use_max_investment_cost = document.getElementById('use_max_investment_cost').checked;
    data.user_defined_battery_size = document.getElementById('user_defined_battery_size').value;
    data.user_defined_cells = document.getElementById('user_defined_cells').value;

    console.log('Sending data:', data); // Debugging statement
    fetch('/update_parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('result').innerText = `Error: ${data.error}`;
        } else {
            const yearlySavings = data.yearly_cost_without_panels_and_battery - data.yearly_cost;
            const paybackPeriod = data.payback_period;
            document.getElementById('result').innerHTML = 
                `<table class="table table-bordered mt-4">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td data-label="Parameter">Panels</td><td data-label="Value">${data.panels}</td></tr>
                        <tr><td data-label="Parameter">Battery Capacity</td><td data-label="Value">${data.battery_capacity} Wh</td></tr>
                        <tr><td data-label="Parameter">Total Investment Cost</td><td data-label="Value">EUR ${data.total_investment_cost}</td></tr>
                        <tr><td data-label="Parameter">Yearly Cost</td><td data-label="Value">EUR ${data.yearly_cost}</td></tr>
                        <tr><td data-label="Parameter">Yearly Cost without Battery</td><td data-label="Value">EUR ${data.yearly_cost_without_battery}</td></tr>
                        <tr><td data-label="Parameter">Yearly Cost without Panels and Battery</td><td data-label="Value">EUR ${data.yearly_cost_without_panels_and_battery}</td></tr>
                        <tr><td data-label="Parameter">Energy Taken with Battery</td><td data-label="Value">${data.energy_taken_with_battery} Wh</td></tr>
                        <tr><td data-label="Parameter">Energy Taken without Battery</td><td data-label="Value">${data.energy_taken_without_battery} Wh</td></tr>
                        <tr><td data-label="Parameter">Self-Sufficiency with Battery</td><td data-label="Value">${data.self_sufficiency_with_battery}/10</td></tr>
                        <tr><td data-label="Parameter">Self-Sufficiency without Battery</td><td data-label="Value">${data.self_sufficiency_without_battery}/10</td></tr>
                        <tr><td data-label="Parameter">Yearly Injected Energy with Battery</td><td data-label="Value">${data.total_energy_injected_with_battery} Wh</td></tr>
                        <tr><td data-label="Parameter">Yearly Injected Energy without Battery</td><td data-label="Value">${data.total_energy_injected_without_battery} Wh</td></tr>
                        <tr><td data-label="Parameter">Yearly Savings</td><td data-label="Value">EUR ${yearlySavings}</td></tr>
                        <tr><td data-label="Parameter">Payback Period</td><td data-label="Value">${paybackPeriod}</td></tr>
                    </tbody>
                </table>`;
        }
    })
    .catch(error => {
        document.getElementById('result').innerText = `Error: ${error}`;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const formElement = document.getElementById('form');
    if (formElement) {
        formElement.addEventListener('submit', submitForm);
    } else {
        console.error('Form element not found');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const useMaxInvestmentCostCheckbox = document.getElementById('use_max_investment_cost');
    const maxInvestmentCostGroup = document.getElementById('max_investment_cost_group');

    // Function to toggle the visibility of the max investment cost input field
    function toggleMaxInvestmentCost() {
        if (useMaxInvestmentCostCheckbox.checked) {
            maxInvestmentCostGroup.style.display = 'block';
        } else {
            maxInvestmentCostGroup.style.display = 'none';
        }
    }

    // Initial toggle based on the checkbox state
    toggleMaxInvestmentCost();

    // Add event listener to the checkbox
    useMaxInvestmentCostCheckbox.addEventListener('change', toggleMaxInvestmentCost);
});

document.getElementById('goal').addEventListener('change', function() {
    var goal = this.value;
    var targetPaybackPeriodContainer = document.getElementById('target_yearly_cost_group');
    if (goal === 'target_cost') {
        targetPaybackPeriodContainer.style.display = 'block';
    } else {
        targetPaybackPeriodContainer.style.display = 'none';
    }
});

document.getElementById('parametersForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var formData = new FormData(this);
    var data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Convert necessary fields to float or integer

    fetch('/update_parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Handle the response data
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});