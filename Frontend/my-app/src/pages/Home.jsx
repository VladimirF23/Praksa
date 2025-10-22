import React from 'react';
import { useSelector } from 'react-redux';

const Home = () => {
    //  state.auth.solarSystem
    const solarSystem = useSelector((state) => state.auth.solarSystem);
    const approvedStatus = solarSystem?.approved;
    // Opcionalno, proverite i loading state da bi se izbeglo prikazivanje greske
    const isLoading = useSelector((state) => state.auth.loading);

    const  user  = useSelector((state)=> state.auth.user);
    // 1. Definicija Poruka na osnovu statusa
    let messageComponent;
    let color;

    if (isLoading) {
        // Prikazuje se dok se proverava authenfikacija (auth check)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#3B82F6" }}>Loading system status...</h2>
            </>
        );
        color = "#3B82F6"; // Plava
    } else if (!solarSystem) {
        // Ako korisnik nema registrovan solar_system (sto ne bi trebalo da se desi nakon registera)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#F59E0B" }}>No Configured System</h2>
                <p style={{ fontSize: "1rem", color: "#D97706", marginTop: "0.5rem" }}>
                    Please register your solar system so you can start tracking your solar data.
                </p>
            </>
        );
        color = "#F59E0B"; // Zuta
    } else if (approvedStatus === 0) {
        // approved = 0 (NIJE ODOBRENO)

        if(user?.user_type=="regular"){
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#DC2626" }}>ALERT: Solar Configuration hasn't been approved by admin</h2>
                <p style={{ fontSize: "1rem", color: "#EF4444", marginTop: "0.5rem" }}>
                    Admin team didnt yet approve your Solar Configuration. 
                    Shown data about production/consumption can be wrong.
                </p>
            </>
        );
        color = "#DC2626"; // Crvena
        }else{
       messageComponent = (
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#DC2626" }}>Welcome admin</h2>

            );
        }
    } else {
        // approved = 1 (ODOBRENO)
        messageComponent = (
            <>
                <h2 style={{ fontSize: "1.2rem", fontWeight: "600", color: "#10B981" }}>Solar Configuration is Approved</h2>
                <p style={{ fontSize: "1rem", color: "#059669", marginTop: "0.5rem" }}>
                    Your Solar Configuration is approved by our admins. 
                    Metering and Simulation data are correct and reliable.
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