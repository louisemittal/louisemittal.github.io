library (worldmet)

met = importNOAA(code = "037683-99999", year = c(2020:2024))
met = subset (met, select = c(code, station, date, air_temp))

write.csv(met, "metdata.csv")
