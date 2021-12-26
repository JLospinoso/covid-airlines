install.packages(c("plm", "zoo"))

library(zoo)
d = read.csv("panel.csv")
d$ts = as.yearqtr(paste(d$year, d$quarter, sep='-'))
coplot(d$covid_cases ~ d$year)

library(plm)
summary(res.re <- plm(d_covid_cases~aggregate_inbound_cases + log(population), 
             index=c("state", "ts"), data=d, model="random"))
