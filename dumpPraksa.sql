CREATE DATABASE IF NOT EXISTS solar_app_db;
USE solar_app_db;

-- 1. Users Table
-- Cuva info o user-u i koordinate njegove kuce
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,                         -- primary key je int koji se autoinkrementuje tako olaksavamo join i ako username se menja to nece biti problem posto on nije unique key 
    username VARCHAR(255) NOT NULL UNIQUE,                          -- unique za login
    email VARCHAR(255) NOT NULL UNIQUE,                             -- za notifikacije u buducnosti
    password_hash VARCHAR(255) NOT NULL,                            -- bcrypt hash
    user_type ENUM('admin', 'regular') NOT NULL DEFAULT 'regular',  -- 'Globaladmin' ili 'regular'
    house_size_sqm DECIMAL(10, 2) NOT NULL,                         -- Velicina kuce u m^2
    num_household_members INT NOT NULL,                             -- broj ukucana
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,          -- Kada se registrovao -> potrebno zbog kasnije simularacije proizvodnje/potrosnje u proslosti od ovog datuma krece simulacija
    
    
    latitude DECIMAL(10, 7) NOT NULL,                               -- geografska sirina  (e.g., 7 decimala za  ~1cm preciznost)
    longitude DECIMAL(10, 7) NOT NULL                               -- geografska duzina 

);



-- 2. SolarSystems Table
-- Cuvamo informacije o korisnikovoj konfiguraciji solarnog sistema
-- Korsnik moze da ima samo JEDNU aktivnu solarnu konfiguraciju (radi manje kompleksnosti DB-a i aplikacije) ovo enforce-uje UNIQUE(user_id)
CREATE TABLE solar_systems (
    system_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    system_name VARCHAR(255) NOT NULL,
    system_type ENUM('grid_tied', 'grid_tied_hybrid') NOT NULL,       -- Grid-Tied (nema bateriju), Grid-Tied Hibrid (sa baterijom)
    total_panel_wattage_wp DECIMAL(10, 2) NOT NULL,                   -- Total Watt-peak kapacitet za sve panele (e.g., 5000 for 5kW)
    inverter_capacity_kw DECIMAL(10, 2) NOT NULL,                     -- Inverter kapacitet u kW
    battery_id INT NULL,                                              -- Foreign kljuc ka bateries tabeli ako je hibridni sistem (zato je dozvoljeno null ako nije hib. onda nema bateriju)
    base_consumption_kwh DECIMAL(10, 2) NOT NULL,                     -- Dodato novo polje (izracunato iz m^2 i broja članova)


    -- FOREIGN KEY Constraint-ovi                                     -- Podsetnik strani kljuc obezbedjuje: da vrednosti u jednoj tabeli odgovaraju vrednostima u drugoj tabeli tj da nema sirocadi, user_id u ovoj tabeli mora postojati u tabeli users
                                                                      -- takodje regulise automatski brisanje i azuziranje pomocu ON DELETE i ON UPDATE, znaci ako se user obrise u tabeli users obrisace se solarni sistem koji je imao fk na taj id u tabeli users
                                                                      -- Foreign key ne osigurava jedinstvenost tj isti user_id se moze pojaviljivati vise puta u ovoj tabeli, osim ako EKSPLICITNO ne stavimo UNIQUE na FK kao u ovoj tabeli
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,-- Ako se obrise user u tabeli users brise se i njegov solarni sistem
    FOREIGN KEY (battery_id) REFERENCES batteries(battery_id) ON DELETE SET NULL, 

    UNIQUE (user_id)                                                  -- Osiguravamo jedinstvenost tj da jedan user moze da ima samo 1 solarni sistem
);


-- 3. Batteries Table (Opcionalno ali je dobro jel mogu da bolje opisem bateriju)
-- NA FRONTENDU OGRANICI  2 tipa baterija sa odredjinim kapacitetima i onda cu dozvoliti da user samo moze da registruja 1 od ta 2 tipa, a u bazi podataka ce oni imati razlicite id-eve
-- da bi mogao da 
CREATE TABLE batteries (
    battery_id INT AUTO_INCREMENT PRIMARY KEY,
    system_id INT UNIQUE,                                               -- Osiguramo da 1 solarni sistem moze max 1 bateriju da ima, takodje moze biti null ako solarni system jos nije kreiran
    model_name VARCHAR(255),                                            -- i tako nemamo onu zavisnost minimalnog kardinaliteta da je 1 vec je sada 0 
    capacity_kwh DECIMAL(10, 2) NOT NULL,                               -- Kapacitet u Kilowat casovima
    max_charge_rate_kw DECIMAL(10, 2),                                  -- Max snaga punjenja u kW   -> detaljnije istrazi o ovim parametrima
    max_discharge_rate_kw DECIMAL(10, 2),                               -- Max snaga praznjenja u kW
    efficiency DECIMAL(4, 2),                                           -- Punjenje/praznjenje efikanost (e.g., 0.95 for 95%)
    manufacturer VARCHAR(255)
    current_charge_percentage DECIMAL(5,2) DEFAULT 0.00                -- Trenutna napunjenost baterije u %
 
);


-- 4. IoT_Devices Table
-- Cuva registrovane korisnikove IoT uredjaje
CREATE TABLE iot_devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,                                               -- FK ka users table
    system_id INT,                                                      -- FK ka solar_systems (opciono: neki uredjaji nisu deo sistema)
    device_name VARCHAR(255) NOT NULL,                                  --  'Bojler', 'Klima', 'Ves masina'
    device_type VARCHAR(100),                                           --  'Water Heater', 'AC', 'Washing Machine' (za kategorizaciju imacu tipa 3 osnovne kategirija i po 3 uredjaja maks)
    base_consumption_watts DECIMAL(10, 2) NOT NULL,                     -- Baseline potrosnja kada su aktivni (u Wat-ima)
    priority_level ENUM('critical', 'medium', 'low', 'non_essential') NOT NULL DEFAULT 'medium', -- Za automatizaciju gasenje onih non-essential prvo
    current_status ENUM('on', 'off') NOT NULL DEFAULT 'off',            -- stanje uredjaja (simulated)
    is_smart_device BOOLEAN NOT NULL DEFAULT FALSE,                     -- True ako je  'smart' uredjaj koji se moze kontrolisati preko web-a 
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,   -- Ako se korisnik brise brisu se i njegovi urejdaji
    FOREIGN KEY (system_id) REFERENCES solar_systems(system_id) ON DELETE SET NULL -- Ako se sistem obrise, uredjaji ostaju ali bez vezanog sistema

);




-- 5. user_hourly_energy_data Table
-- Cuvamo (satnu) proizvidnju eneregije, potrosnje, korisenjca baterije, uvozenje i vracenje  iz/sa grida
-- npr da bi dobili dnevnu potrosnju koristicemo SQL upit gde cemo sumirati proizvedenu snage,potrosenu i ostale parametre i tako dobiti dnevnu potrosnju 
CREATE TABLE user_hourly_energy_data (
    user_id INT NOT NULL,
    record_datetime DATETIME NOT NULL,                                  -- Specifican sat (npr '2025-07-17 10:00:00')

    -- Energy values in Kilowatt-hours (kWh) for that hour
    solar_production_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    household_consumption_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,    -- satna potrosnja domacinstva
    grid_import_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,              -- uvezena snaga iz grid-a 
    grid_export_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,              -- vracanje snaga u grid
    battery_charge_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,           -- Energija napunjena u bateriju, Pazi kako ovo racunas !!!! ovo zavisi od praznjenja !
    battery_discharge_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,        -- praznjenje baterije

    PRIMARY KEY (user_id, record_datetime),                             -- Composite PK osigurava jedinstvenost da jedan korisnik za jedan sat ima jedinsven info u ovoj tabeli, (NIJE UNIQUE u smisli kao samo 1 user_id moze da se pojavi vec kombinacija sa satom je unique)
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- 6. user_daily_energy_summary Table
-- Cuvamo dnevnu produkciju energije i potrosnje itd, tj sume od satne proizvodne
CREATE TABLE user_daily_energy_summary (
    user_id INT NOT NULL,
    record_date DATE NOT NULL,                                          --  specifican datum (npr '2025-07-17' ovakva forma datuma je zbog Open Weather-a)

    -- Energy values in Kilowatt-hours (kWh)
    solar_production_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    household_consumption_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    grid_import_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,              -- Engerija povucena iza grida
    grid_export_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,              -- Engerija vracen-a u grid
    battery_charge_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,           -- Energija napunjenja u  bateriju
    battery_discharge_kwh DECIMAL(10, 3) NOT NULL DEFAULT 0.000,        -- Energija potrosena iz baterija 

    -- Timestampovi za auditing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Primary kljuc -> jedan potrosnja korisnika za 1 dan
    PRIMARY KEY (user_id, record_date),

    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

