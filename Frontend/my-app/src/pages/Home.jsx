import React from 'react';
import { useSelector } from 'react-redux';

const Home = () => {
    //  state.auth.solarSystem
    const solarSystem = useSelector((state) => state.auth.solarSystem);
    const approvedStatus = solarSystem?.approved;
    // Opcionalno, proverite i loading state da bi se izbeglo prikazivanje greske
    const isLoading = useSelector((state) => state.auth.loading);


    // 1. Definicija Poruka na osnovu statusa
    let messageComponent;
    let color;

    if (isLoading) {
        // Prikazuje se dok se proverava authenfikacija (auth check)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#3B82F6" }}>Učitavanje statusa sistema...</h2>
            </>
        );
        color = "#3B82F6"; // Plava
    } else if (!solarSystem) {
        // Ako korisnik nema registrovan solar_system (sto ne bi trebalo da se desi nakon registera)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#F59E0B" }}>Nema Konfigurisanog Sistema</h2>
                <p style={{ fontSize: "1rem", color: "#D97706", marginTop: "0.5rem" }}>
                    Molimo vas da registrujete svoj solarni sistem kako biste počeli sa praćenjem.
                </p>
            </>
        );
        color = "#F59E0B"; // Zuta
    } else if (approvedStatus === 0) {
        // approved = 0 (NIJE ODOBRENO)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#DC2626" }}>PAŽNJA: Konfiguracija Nije Potvrđena</h2>
                <p style={{ fontSize: "1rem", color: "#EF4444", marginTop: "0.5rem" }}>
                    Admin tim još uvek nije potvrdio ispravnost vaše solarne konfiguracije. 
                    Prikazani podaci o potrošnji/proizvodnji mogu odstupati od realnih merenja.
                </p>
            </>
        );
        color = "#DC2626"; // Crvena
    } else {
        // approved = 1 (ODOBRENO)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#10B981" }}>Konfiguracija Sistema je Odobrena</h2>
                <p style={{ fontSize: "1rem", color: "#059669", marginTop: "0.5rem" }}>
                    Vaša solarna konfiguracija je potvrđena od strane administratora. 
                    Merenja i simulacije se smatraju ispravnim i pouzdanim.
                </p>
            </>
        );
        color = "#10B981"; // Zelena
    }

    return (
        <div 
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                minHeight: "80vh",
                flexDirection: "column",
                textAlign: "center",
                padding: "20px"
            }}
        >
            <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "1rem" }}>
                Welcome to Solar Track App
            </h1>
            
            {/* Kontejner za status poruku */}
            <div 
                style={{ 
                    marginTop: '2rem', 
                    padding: '1.5rem', 
                    border: `2px solid ${color}`, 
                    borderRadius: '8px', 
                    maxWidth: '600px',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)'
                }}
            >
                {messageComponent}
            </div>

            <p style={{ fontSize: "1.1rem", color: "#555", marginTop: "2rem" }}>
                Monitor your solar system in real time and manage your energy efficiently.
            </p>
        </div>
    );
};

export default Home;