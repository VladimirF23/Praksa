import { Link, useNavigate } from "react-router-dom";
import { Search, User } from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../features/authorization/authSlice";    // Redux logoaut
import {logoutUser} from "../api/authApi";                      // importujemo API backend call           

//login ce se na drugom mestu desavati posto ce se morati popouniti forma login-a

//search,User su ikonice iz ovog library-a od reacta      

//link za navigaciju izmedju razl URL bez refresh-a aplikacije slizno <a> tagu samo optimizovano za React


/* 
    className je CSS klasa u react-u, bg-> background grey, 
    flex->horizontalno children item-e da stavi, 
    items-center->vertikalno align elemente
    justify-between white space mesta izmedju elementa podjednako pushuje left i right part-ove ka edgovima

    Reddit_logo sam stavio u public jer nema potrebe onda da se importuje i idealno je za static assete kao sto su logo-i, 
    brze ce se loadovati i globalno je dostupno
    alt - text description ako se slucajno ne loaduje logo
*/

const Navbar = () => {
    //State da pratimo da li je user prijavljen

    
    const isAuthenticated = useSelector((state) => state.auth.isAuthenticated);//useSelector((state) => state.auth.isAuthenticated):proverava da li je user privaljen i to gleda u  Redux store-u
    const  user  = useSelector((state)=> state.auth.user);                     //useSelector((state) => state.auth.user) pristupamo user podacima (username, global_admin) storovanim u Reduxu
    const dispatch = useDispatch();
    const navigate = useNavigate()

    const handleLogout = async () => {
        try {
            await logoutUser(); // Call the backend logout API
            dispatch(logout()); // Dispatch Redux logout action
            navigate('/'); // Redirect to login page after logout
        } catch (error) {
            console.error("Logout failed:", error);
            // opcionalno dispatch error ka Redux ako imamo error state za global issues
            // za sad ga log-ujemo. If logout fails uglavnom je backend problem
            // a cisitmo client-side svakako
            dispatch(logout()); // Osiguramo client-side state je ociscen cak i ako API fail-uje
            navigate('/');     // na pocetnu stranicu se navigatujemo
        }
    };




    return (
        // Glavni navbar kontejner sa flex-om da sve bude horizontalno
        <nav className=" bg-gray-800 text-white p-3 !flex items-center justify-between">
            
            {/*  Levo - Logo (uklonjen extra <div> da ne bude vertikalno) */}
            <Link to="/" className="text-2xl font-bold flex items-center">
                <img 
                    src="/solar.png"
                    alt="Solar Logo"
                    className="mr-2"
                    style={{ height: '20px', width: '20px', objectFit: 'contain' }}
                />
                Solar Track
            </Link>

            {/*  Centar - Search bar, dodao sam flex-1 da se prosiri u slobodan prostor */}


            {/*  Desno - MyProfile / Login i Logout */}
            <div className="flex items-center space-x-4">
                {isAuthenticated ? (
                    <>
                        {/* Ikonica User-a i username  ako je ulogovan*/}
                          <Link to="/live-metering" className="px-3 py-1 bg-yellow-500 rounded-lg">Live Metering</Link>

                        <Link to="/profile" className="flex items-center space-x-2">          
                            <User className="text-white" />
                            <span>{user?.username || "MyProfile"}</span>       
                        </Link>
                        {/* Dugme za logout */}
                        <button 
                            onClick={handleLogout}                      //a ne  handleLogout() zato sto ako je zagradam react odma poziva i user se logoutuje bez da se klikne na dugme
                            className="bg-red-500 px-3 py-1 rounded-lg"
                        >
                            Logout
                        </button>
                    </>
                ) : (
                    /* Ako user nije prijavljen, prikazi Login dugme 

                        U Div-u su da bi imali spacing za oba linka
                    */
                    
                    <div className="flex items-center space-x-4">
                    <Link to="/login" className="bg-blue-500 px-3 py-1 rounded-lg">Login</Link>
                    <Link to="/register" className="bg-green-500 px-3 py-1 rounded-lg">Register</Link>
                    </div>

                )}
            </div>
        </nav>
    );
};

export default Navbar;
