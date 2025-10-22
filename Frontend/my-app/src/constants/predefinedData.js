// Predefinisani izbori za input polja
export const SYSTEM_TYPES = [
    { value: 'grid_tied', label: 'Grid Tied (Nema bateriju)' },
    { value: 'grid_tied_hybrid', label: 'Grid Tied Hybrid (Ima bateriju)' }
];

export const PREDEFINED_BATTERIES = [
    { 
        id: 1,                              //ovi ID su lokalni tj vaze samo na frontend-u i potrebni su nam cisto da znamo sta je korisnik selektovao A NA BACKEND-u ce se u bazi automatski dodeliti podaci
        name: "Solar Battery X (10 kWh)", 
        manufacturer: "SunPower",
        capacity_kwh: 10.0,
        max_charge_rate_kw: 5.0,
        max_discharge_rate_kw: 5.0,
        efficiency: 0.92,
        image: '/battery.jpg' 
    },
    { 
        id: 2, 
        name: "EcoVolt Storage (7 kWh)", 
        manufacturer: "EcoPower",
        capacity_kwh: 7.0,
        max_charge_rate_kw: 3.5,
        max_discharge_rate_kw: 3.5,
        efficiency: 0.90,
        image: '/battery.jpg'
    },
];

export const PREDEFINED_IOT_DEVICES = [
    { 
        id: 101, 
        device_name: "Smart Fridge", 
        device_type: "Appliance",
        base_consumption_watts: 150,
        priority_level: "critical", 
        is_smart_device: true,
        image: '/fridge.png'
    },
    { 
        id: 102, 
        device_name: "EV Charger (7kW)", 
        device_type: "EV",
        base_consumption_watts: 7000,
        priority_level: "medium", 
        is_smart_device: true,
        image: '/ev_charger.jpg'
    },
    { 
        id: 103, 
        device_name: "Smart AC", 
        device_type: "AC",
        base_consumption_watts: 2000,
        priority_level: "medium", 
        is_smart_device: true,
        image: '/ac_unit.jpg'
    },
];