const Home = () =>{
    return (
    <div 
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "80vh",
        flexDirection: "column",
        textAlign: "center"
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "1rem" }}>
        Welcome to Solar Track App
      </h1>
      <p style={{ fontSize: "1.1rem", color: "#555" }}>
        Monitor your solar system in real time and manage your energy efficiently.
      </p>
    </div>
  );
};

export default Home;