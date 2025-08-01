
#Service/SimulationService.py
#najbolje da koristis onu INSTANT opciju za ove parametre tako ces dobiti najbolje podatke

# Funkcije nisu dirketno povezane (da jedna drugu zovu unutar racunanje zato sto onda unit testovi ne bi bili moguci za razlicite podatke)
# Ali ce se ovim redom pozivati da bi dobili zeljene stvari

# 1.Izracunaj solar_production_kw.

# 2.Izracunaj household_consumption_kw.

# 3.Izracunaj net_power_kw = solar_production_kw - household_consumption_kw.

# 4.Pozovi update_battery_charge sa net_power_kw da dobiješ new_charge_percentage i actual_battery_flow_kw.

# 5.Pozovi calculate_grid_contribution sa solar_production_kw, household_consumption_kw i actual_battery_flow_kw.



# 1. Irradience (zracenje) vs Radiation (Energije Zracenja)
#   a) Irradience: Snaga po jedinic povrsine, obicno u wat-ima po kvadratnom metru (W/m^2), ovo je TRENUTNA vrednost, ovo je kao koliko je sunce jako u ovom trenutku
#   b) Radiation:  Energija po jedinici povrsine   J/m^2 (dzuli) ili Vat-satima po m^2. Ovo se akumilira u toku nekog perioda npr sat / dan, OpenMeteo koristi 'radiation' da oznaci irradiance prosecno tokom proteklog sata sto zbunjuje

# 2. GHI (Global horizontal Irradience -> Globalno horizontalno zracenje)
#   Ukupno trenutno kratkotalasno zracenje primljeno od suna na horizonatlanoj porvsini na Zemljinoj povrsini
#   ukljucuje direktnu suncevu svetlost i difuznu suncevu svetlost (rasutu atmosferom)
#   Komponente: GHI = DHI + Direct_Horiozntal_Irradience (Direct_Horizontal je  = DHI * cos(solar_zenith_angle))
#   Upotreba: GHI se najcese koristi i najlaksije za koriscenje prilikom jednostavnih kalkulacija kada ne znam tacan Nagib i Azimuth panela ili ako su mi paneli ravni


# 3. DNI (Direct Normal Irradiance) -> Direktno normalno zracenje
#   Trenutno solarno zracenjenje primljeno od sunca u pravcu NORMALNOM na POVRSINU. Ovo je cista sunceva svetlost koja baca Ostru senku. NE ukljucuje rasutu svetlost
#   Upotreba: Krucijalno ako znamo tacnu orijentaciju i nagib panela ili za sisteme koje  prate kreanje sunca

#4. DHI (Diffuse Horizontal Irradiance) -> Difuzno horiontalno Zracenje
#   Tretno solarno zracenje primljeno od sunca, rasuto atmosferom i oblacima na horizontalnoj povrsini. Ovo je svetlost koja idalje osvetljava stvari po OBLACNOM VRMEENU cak i ako nema dirketnog sunca
#   Upotreba: Uvek je potrebno kada se DNI koristi za izracunavnje GHI ili kao komponenta GHI


#5. DSR (Direct Solar Radition)


#6.GTI (Global Tilted Radiation)  (Instant):
#   Ukupno trenutno kratkotalasno zracenje primljeno na povrsini (sol .panelima) koja je nagnuta pod odredjenim uglovm i okrenuta ka odredjenom azimutu (pravcu). 
#   Upotreba: OVO JE NAJPRECIZNIJ PODATAK ako znas tacnu fizicku orijentaciju panela
#   Razmisljam da dodam azimut i pravac u DB za svakoj user-a 



# za ovu funkciju koristicemo Global Tited Raditation GTI(instant), Temperature2m, is_day -> da osiguram da je nocu proizvodnja 0
def calculate_solar_production(solar_system_config: dict, weather_data: dict) -> float:
    """"
    Cilj funkcije:
        Izracunati trenutnu snagu u kiloWatima (kW) koju solarni paneli trenutno generisu u datom momentu uzimajuci u obzir uslove okoline i karakteristike panela
        Ova funkcija omogucava da simuliram realisticnu proizvodnju solarnih panela uzimajuci u obzir kljucne faktore koje uticu na njihov rad. Korisnjem 'instant' GTI vrednosti (trebace mi tild i azimuth) i temperaturnog koeficienta
        dobijemo sliku trenutne snage sistema
    Teorija:
        Izlazna snaga solarnih panela je direktno proporcionalna kolicini sunacane svetlosti (Solarnom Zracenju) koja pada na njihovu povrinu i njihovoj nominalnoj snazi
        Medjutim na Efikasnost i samim tim na stvarnu izlaznu snagu uticu i drugi faktori. Najvazniji od njih su Temperatura Panela i razni gubici u samom solarnom sistemu (kod invertera npr)  
        Formulu koju koristim modelira ove faktore kako bi se od nominalne (IDEALNE u lab. uslovima) snage doslo do realisticne trenutne proizvodnje
    
    Formula:
        P_solarna_kW = P_nominalna_Wp * (I_STVARNA / I_STC) * Eff_sistema * Eff_temp
        
        P_solarna_kW   ->  Trenutna solarna proizvodnja u kilovatima (kW). To je rezultat koji zelimo da dobijemo.
        P_nominalna_Wp ->  Nominalna snaga panela u wat-pikovima (Wp), Proizvodjaci solarnih panela odredjuju ovu snagu pod Standardnim uslovima, ovo su idealni labaratorisjki uslovi, Temp panela 25 C i solarno zracenje 1000 W/m^2, predstavlja nominalni zbir svih panela u korisnikovom sistemu
        .                  To je max snaga koju sistem moze da proizvede u idealnim uslovima

        I_STVARNA/I_STC->  Korekcija za stvarno solarno zracenje, u teoriji solarni paneli proizvode vise energije kada je sunce jace, ovaj deo formule skalira Nominalnu snagu na osnovu toga koliko je Stvarno zracenje u poredjenju sa referetnim zracnjem (I_STC)

        I_STVARNA      ->  GTI (Global Tilted  Radiation) iz OpenMeteoAPI (ili iz UNIT TESTA) u code-u je ovo actual_irradience_wpm2, Ovo je NAJRELAVATNIJA VREDNOST za moj proracun, Predstavlja ukupno trenutno zracenje direktno i difuzno koje pada na konkretnu nagnututu i orejntisanu povrsinu (solarne panele)
                           Ako korisnik unese nagib (tilt) i azimut, OpenMeteo ce vratiti vrednost koja vec preracunata za tu specificnu orijentaciju sto pojednostavljujue proracun
        I_STC          ->  Fiksna vrednost od 1000 W/m^2, referetno zracenje pod STC (lab. uslovima)

        Eff_sistema    -> U realnom svetu solarni sistemi nikada ne rade na 100% efikasnosti nominalne snage zbog raznih gubitaka koji se desavaju izmedju panela i mesta potrosnje:
        .                 a) Efikanost invertera: DC struja koju proizvode paneli mora se pretvoriti u AC za kucnu upotrebu, pri cemu se gubi deo energije (2-5%)
        .                 b) Gubici u provodnicima (otpor u el kablovima dovodi do malih gubitaka) ,Priljavstina i Sencenje smanjuje se kolicina sunceve svetlosti koja dolazi do panela ...
        .                 Vrednost: ovo je empirijski faktor  i koristise za aproksimaciju svih gubitaka. Realna vrednost od 75% do 85%. Koristicu 80% kao kompromis za generalnu simulaciju
        
        
        Eff_temp        -> Efikasnost Solarnih panela opada kako temperatura raste (iako proizvode struju zahavljujuci suncevoj svetlosti) oni bolje rade pri nizim temperaturama To je zato sto visoke temperature povecavaju otpor u poluprovodnickim materijalima, sto smanjuje napon i posledicno i snagu        
        .               -> Formuala: Eff_temp = 1 - (T_stvarna - T_ref) * gamma
                        -> T_stvarna je stvarna temperatura panela u °C, iako OpenMeteo daje temperature_2m (ambijentalna temperatura vazduha), solarni paneli se mogu zagrejati mnogo vise od okolnog vazduha, pogotovo na direktnom suncu. U slozenijem modelu bih koristio proracun temperature celije ali ovde za moju aplikaciju cu koristiti temperature_2m
                           kao aproksimaciju jer je dovoljno precizno za pocetak uz malo agresivniji koeficijent
                        -> T_ref je referetna temperatura obicno 25 °C (u lab se na ovoj temp mere performanse panela)
                        -> gamma (temp_coeff u code-u), temperaturni koeficijent snage. Ovo je obicno negativna vrednost koju prozvodjacji daju npr -0.4 % tj -0.004. Ona govori za koliko % opada efikasnost panela za svaki stepen Celzijusa iznad T_ref (0.4% se uobicajeno koristi)

                        -> primer  ako je temperature_2m = 35 °C   razlika je 10°C (35-25). Efikasnost je  10 * 0.004 tj 4% pa je Eff_temp = 1 - 0.04 => 0.96 

        Finalno:  KONACNA PROIZVODNJA: Ogranicavamo proizvodnju na kapacitet invertera.
                 Sistem ne moze proizvesti vise snage nego sto inverter moze da obradi
                 final_production_kw = min(potential_production_kw, inverter_capacity_kw)
    """ 

    # uzimamo od API-a ili od unit testa
    # ambijentalna temp za racunjanje gubitka efikasnosti zbog temperature, ovo predstavlja temperaturu panela
    temperature_2m = weather_data.get("temperature_2m", 25.0)

    # Provera da li je dan  (0 = noc, 1  =dan)
    # ako je noc proizvodnja je 0
    is_day  = weather_data.get("is_day",0)

    #ako je noc nema proizovdnje
    if is_day==0:
        return 0


    # Dobijanje kapaciteta invertera iz konfiguracije sistema (kW)
    # Inverter je usko grlo; ne moze da obradi više snage od svog kapaciteta.
    inverter_capacity_kw = solar_system_config.get("inverter_capacity_kw", 0.0)

    #Nominalna snaga panela iz konfiguracije sistema Wp - Watt-peak
    # Ovo je ukupna snaga svih panela u sistemu pod standardnim uslovima testiranja.
    total_panel_wattage_wp = solar_system_config.get("total_panel_wattage_wp", 0.0)


    # Dobijanje instant (trenutnog) Global Tilted Radiation (GTI) iz vrmeneskih podataka (W/m^2)
    # ovo je napreciznije zracenje jer je vec proracunat nagib i azimut panela
    # OpenMeteo vraca ovu vrednos ako su tilt i azimut prosledjeni API pozivu
    actual_irradiance_wpm2 = weather_data.get("global_tilted_irradiance_instant",0.0) # I_STVARNA

    # Standardni uslovi testiranja (STC) - referetno zracenje
    # nominalna snaga panela je definisana pri zracenju
    I_STC = 1000.0      # W/m^2

    # Faktor sistemski gubitaka system_efficiency_factor
    # gubitci u sistemu smanjuju efikasnost (gubitci kod invertera,provodnika, prljavstina)
    # emprijiska vrednost  80% uobicajena aprox.
    eff_system = 0.80        

    # referetna temp i Temperaturni koeficient 
    # Za svaki stepen iznad referetne temp efikasnost panela opada za 0.4 % (0.004)
    temp_ref = 25.0 
    temp_coef = 0.004

    # Izracunavanje faktora efikasnosti zbog temperature (eff_temp)
    # Koristimo max(0, ...) da osiguramo da se efikasnost ne povecava (ako je temp < 25 onda ako nema max bi se efikasnost povecavala u realnosti se malo povecava efikasnost za temp < ref al to ovde zanemarujemo)
    # moj model to pojednostavljuje i fokusira se pad efikasnosti pri visokim temp
    eff_temp = 1.0 - max(0, (temperature_2m - temp_ref) * temp_coef) 



    # Glavna formula

    #  jedinica: (Wp / (W/m2)) * (W/m2) * (bezdimenzionalno) = W
    #  delimo sa 1000 da dobijemo kW
    production_kw = (total_panel_wattage_wp * (actual_irradiance_wpm2 /I_STC) * eff_system * eff_temp) /1000        


    #KONAcNA PROIZVODNJA: Ogranicavamo proizvodnju na kapacitet invertera.
     #            Sistem ne moze proizvesti vise snage nego sto inverter moze da obradi
    final_production_kw = min(production_kw, inverter_capacity_kw)
    


    return max(0.0, final_production_kw)            #Osiguravamo da bude pozitivno ili 0  (ne moze biti negativna proizvodnja)

def calculate_household_consumption(user_config: dict,solar_system_config:dict, iot_devices_data: list[dict]) -> float:
    """
        Cilj funkcije:
            Izracunati trenutnu UKUPNU elektricnu snagu potrosnje domacinstva u KW


        Teorija(kojom se vodim):
            Potrosnja se deli na dva dela: 
            1. Bazna potrosnja (gde spadaju uredjaji koji su stalno ukljuceni i neka nasa aproksimacija koju smo izracunali preko funkcije calculate_base_consumption)
            2. Potrosnja IoT uredjaja: Ovo je dodatna snaga koju trose IoT uredjaji kada su ukljuceni snaga uredjaj se meri u Watima

        Formula:
            P_potrosnja_kw = P_bazna_kw + ∑ (P_iot_uredjaj_potrsnja_w za aktivne uredjaje)

            P_potrosnja_kw -> ukupna trenutna elektricna snaga koju domacinstvo trosi
            P_bazna_kw     -> ovo smo izracunali preko calculate_base_consumption

            ∑ P_iot_uredjaj_potrsnja_w za aktivne uredjaje -> zbir snaga svih ukljuceni IoT, potrebno ih konvertovati u kW


    """
    base_consumption_kw = solar_system_config.get("base_consumption_kw", 0.0)
    # Izracunavanje potrošnje IoT uređaja
    # Inicijalizujemo ukupnu snagu koju troše IoT uredjaji na 0.
    iot_consumption_watts = 0.0
    for device in iot_devices_data:
        # Ako je uredjaj ukljucen dodajemo njegovu baznu potrosnju snage.
        # Pretpostavljamo da je 'base_consumption_watts' u watima (W).
        if device.get("current_status") == "on":
            iot_consumption_watts += device.get("base_consumption_watts", 0.0)

    # Pretvaramo ukupnu snagu potrosnje IoT uredjaja iz vati (W) u kilovate (kW).
    total_iot_consumption_kw = iot_consumption_watts / 1000.0

    # Ukupna trenutna snaga potrosnje domacinstva
    # Sabiramo baznu snagu i ukupnu snagu aktivnih IoT uredjaja.
    total_household_consumption_kw = base_consumption_kw + total_iot_consumption_kw

    return total_household_consumption_kw


def calculate_grid_contribution(solar_production_kw: float, household_consumption_kw: float, battery_flow_kw: float) -> float:
    """
    Cilj funkcije:
        Izracunati trenutnu neto razmenu elektricne snage između domaćinstva i distributivne mreze u kilovatima (kW).
        Ova funkcija određuje da li domaćinstvo trenutno uzima snagu iz mreze (uvoz) ili šalje snagu u mrezu (izvoz).

    Teorija:
        Energetski bilans u domaćinstvu sa solarnim panelima i baterijom (ako je ima) zasniva se na principu ocuvanja energije.
        Ukupna snaga koja se troši u domaćinstvu mora biti pokrivena nekim izvorom. Ti izvori su:
            1. Solarna proizvodnja: Snaga koju generišu solarni paneli.
            2. Baterija: Snaga koju baterija isporucuje (praznjenje) ili apsorbuje (punjenje).
            3. Distributivna mreza: Snaga koja se uzima iz mreze ili se u nju šalje.

    Formula:
        P_mreza_kW = P_potrosnja_kW - P_solarna_kW + P_protok_baterije_kW

        Objašnjenje elemenata formule:
            P_mreza_kW: Trenutna neto razmena snage sa mrezom u kilovatima (kW).
                - Pozitivna vrednost: Znaci da domaćinstvo uzima (uvozi) snagu iz mreze. To se dešava kada je ukupna potrošnja veća od solarne proizvodnje i snage koju baterija moze da isporuci.
                - Negativna vrednost: Znaci da domaćinstvo šalje (izvozi) snagu u mrezu. To se dešava kada je solarna proizvodnja veća od ukupne potrošnje i snage koju baterija moze da apsorbuje.

            P_potrosnja_kW: Ukupna trenutna elektricna snaga potrošnje domaćinstva u kilovatima (kW).
                            Ova vrednost dolazi iz funkcije `calculate_household_consumption` i predstavlja zbir bazne potrošnje i potrošnje svih aktivnih IoT uređaja.
                            To je ukupna snaga koju kuća "zahteva" u datom trenutku.

            P_solarna_kW: Trenutna elektricna snaga koju proizvode solarni paneli u kilovatima (kW).
                          Ova vrednost dolazi iz funkcije `calculate_solar_production`.

            P_protok_baterije_kW: Trenutni protok snage ka ili iz baterije u kilovatima (kW).
                                  Ova vrednost dolazi iz funkcije `update_battery_charge`.
                                  - Ako je `P_protok_baterije_kW` pozitivan (baterija se puni), to znaci da baterija apsorbuje snagu. Ta snaga se dodaje ukupnoj potrebi domaćinstva, što rezultira većom potrebom iz mreze ili manjim izvozom.
                                  - Ako je `P_protok_baterije_kW` negativan (baterija se prazni), to znaci da baterija isporucuje snagu. Ta snaga smanjuje ukupnu potrebu domaćinstva iz mreze, što rezultira manjim uvozom ili većim izvozom.
    """

    # Ova funkcija izracunava trenutnu neto razmenu elektricne snage sa distributivnom mrezom (u kW).
    # grid_contribution_kw > 0  znaci da domacinstvo uvozi iz grid-a
    # grid_contribution_kw < 0  znaci da domacinstvo exportuje u grid

    # ovde se se namerno oduzimao od consumption-a da bi nam ostao negativan znak ako je  solar_production_kw veci od household_consumption_kw
    net_demand_or_surplus = household_consumption_kw - solar_production_kw

    # battery_flow_kw ce se dobijati iz update_battery_charge i ta funkcija nam garantuje da se nece desiti npr imamo production=1kW  consumption = 3kW  i da bude pozitivan(da on se puni tj da trosi) battery_flow_kw = 3kW 
    # jer bi to onda znacilo da cemo i za njega import-ovati iz GRID-a A TO SE NE RADI ! ! !

    # battery_flow_kw > 0  on se puni i bice pozitivan samo kada je net_demand_or_surplus (solar_production_kw)  > od potrosnje 

    # battery_flow_kw <0   on doprinosi da se uvoz iz grid-a smanji kada imamo potrosnja > proizvodnje,  i ako baterija moze da ispegla npr net_demand_or_surplus = 3 kW (sto znaci treba uvest iz grid-a) i battery_flow_kw= - 5k  znaci baterija se prazni i pomaze da se ispegla potrosnja
    # grid_contribution_kw bi trebao da bude 0 tj da se nista ne uvozi iz grid-a 

    

    grid_contribution_kw = net_demand_or_surplus + battery_flow_kw

    return grid_contribution_kw

def update_battery_charge( battery_config: dict, net_power_kw: float, time_step_hours: float) -> tuple[float, float]:
    """
        Cilj funkcije:
                    Izracunati novo stanje napunjenosti baterije (u %) i stvarni prokot snage ka ili iz baterije u kW tokom odredjenog vremenskog perioda

        Teorija: 
                    Baterija u solarnom sistemu sluzi kao skladiste energije, ona se puni kada solarni paneli proizvode vise snage nesto sto domacinstvo trosi a prazni se kada 
                    Domacinstvo trosi vise snage nego sto paneli proizvode. Proces punjnja i praznjenja baterije nije 100% efikasan i ogranicen je njenim kapacitetomi maksimalnim brzinama punjenja/praznjenja

        Formula:
                
        

        net_power_kw            -> Ovo je razlika izmedju snage koju solarni paneli proizvode i snage koju  domacinstvo trosi
        .                            net_power_kw >0 -> znaci postoji visak snage (Proizvodnja > Potrosnje) ova snaga se moze koristiti za punjenje baterije
        .                            net_power_kw <0 -> Znaci postoji deficit snage (potrosnja > proizvodnja) ovaj deficit se moze pokriti praznjenm baterije ili uzimanjem snage iz mreze (ako je baterija prazna ili nepostoji)

        capacity_kwh             -> Ovo je max kolicina energije u (kWh) koju baterija moze da uskladisti, ne moze ici preko svog kapaciteta niti prazniti se ispod 0%

        max_charge_rate_kw       -> baterije imaju ogranicenje koliko brzo mogu da prime ili isporuce snage, cak i ako ima viska snage za punjenje baterija se moze puniti samo do svoje max brzine punjenje isto i za praznjenje
        max_dicharge_rate_kw     -> -||- samo za praznjenje

        efficiency               -> efikasnost punjenja i praznjenja baterije, deo energije se gubi kao toplota


        time_step_hours          -> Radi se o simulaciji tokom vremena pa uzimamo u obzir koliko traje jedan korak/period simualcije (npr 1 minut =1/60 sata)
        .                            Snaga kw se mnozi vremenom h da bi se dobila energija kWh
     """
    # Dobijanje konfugiracionih parametara
    capacity_kwh = battery_config.get("capacity_kwh", 0.0)
    current_charge_percentage  = battery_config.get("current_charge_percentage", 0.0)
    max_charge_rate_kw = battery_config.get("max_charge_rate_kw", 0.0)
    max_discharge_rate_kw = battery_config.get("max_discharge_rate_kw", 0.0)
    efficiency = battery_config.get("efficiency", 1.0)                      # Efikasnost (npr. 0.9 za 90%)


    current_charge_kwh = (current_charge_percentage /100.0) * capacity_kwh  # da dabojimo trenutno napunjenost u kWh

    #Ako baterija nema kapacitet (neka greska npr prosledjena)
    if capacity_kwh <= 0:
        return 0.0, 0.0

    
    actual_battery_flow_kw = 0.0                                            # Stvarni protok snage ka/iz baterije (kW), >0 onda se baterija puni, <0 onda se baterija prazni
    charge_change_kwh = 0.0                                                 # Promena napunjenosti baterije u kWh

    # Ako nije proizvodnja > potrosnje, onda se baterija nece puniti 
    # vec ce se pokusati da izvucemo energiju iz baterija da to izbalansiramo ako baterija moze da pokrije potrosnju



    if net_power_kw>0:                                                      # postoji visak snage Proizvodnja > Potrosnje  -> pokusavamo da punimo bateriju
        energy_available_kwh = net_power_kw * time_step_hours               # Koliko energije je dostupno za punjenje
        max_charge_by_rate_kwh = max_charge_rate_kw * time_step_hours           # Maksimalna energija koju baterija moze primiti po brzini
        remaining_capacity_kwh = capacity_kwh - current_charge_kwh          # Koliko kWh još moze da stane u bateriju

        # Stvarna energija koja ulazi u bateriju je minimum od
        # 1. Dostupne energije preko proizvodnje solarnih panela (nakon efikasnosti punjenja)
        # 2. Maksimalane energije
        # 3. Preostalog kapaciteta baterije
        charge_amount_kwh = min(
            energy_available_kwh * efficiency,
            max_charge_by_rate_kwh,
            remaining_capacity_kwh
        )
    
        charge_change_kwh = charge_amount_kwh

        actual_battery_flow_kw = charge_change_kwh / time_step_hours
    
    
    elif net_power_kw< 0:                                                   #potrosnja > proizvodnje, sada koristimo ako je moguce bateriju da ispegla bilans na 0
        energy_needed_kwh = abs(net_power_kw) * time_step_hours             #kolko je energije potrebno

        max_discharge_by_rate_kwh = max_discharge_rate_kw * time_step_hours # Maksimalna energija koju baterija moze isporuciti domacinstvu

        # Energija koju ce baterija davati je minum od 
        # 1. Potrebne energije (nakon efikasnosti)
        # 2. Maksimalne energije koju baterija moze isporuciti s obizrom na svoju brzinu praznjenja
        # 3. Trenutne napunjenosti baterije (ne moze se isprazniti vise nego sto ima)

        # u principu ovaj minimum garantuje da uzimamo vrednost u granicama, ako baterija moze da dovoljno energije onda samo uracunamo effiecni uz to kolko ce zapravo dati
        # ako baterija moze da vise energije onda pazimo na njen max_discharge_by_rate_kWh
        # i kranje baterije moze da onoliko energije kolko je ona napunjenja trenutno current_charge_kwh = (current_charge_percentage /100.0) * capacity_kwh  # da dabojimo trenutno napunjenost u kWh
        discharge_amount_kwh = min(
            energy_needed_kwh / efficiency,                             
            max_discharge_by_rate_kwh,
            current_charge_kwh                                          # Ne moze se isprazniti vise nego što je trenutno u bateriji
        )


        charge_change_kwh = - discharge_amount_kwh                      #promena je negativna jer uzimamo energiju iz baterije tj ona se prazni
        actual_battery_flow_kw = charge_change_kwh / time_step_hours

    #Izracunamo napunjenost novu baterije, moze se smanjiti/povecati
    new_charge_kwh= current_charge_kwh + charge_change_kwh

    #osiguramo da nova napunjenost ostane u unutar granica (0% do 100% kapaciteta)


    new_charge_kwh = max(0.0, min(capacity_kwh, new_charge_kwh))


    #sad izracunamo u procentima novu napunjenost

    new_charge_percentage = (new_charge_kwh / capacity_kwh) * 100.0 if capacity_kwh > 0 else 0.0

    return  new_charge_percentage, actual_battery_flow_kw