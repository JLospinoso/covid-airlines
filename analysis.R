# install.packages(c("plm", "zoo"))
library(zoo)
library(plm)

d = read.csv("panel-out.csv")
d$ts = as.yearqtr(paste(d$year, d$quarter, sep='-'))

# Aggregate Inbound

summary(re.cases <- plm(diff(covid_cases) ~ aggregate_inbound_cases 
                        + vaccinated + population + ts, 
                  index=c("state", "ts"), data=d, model="random"))

Box.test(re.cases$residuals)

# Centrality

d$p_covid_cases <- d$covid_cases / d$population
d$p_vaccinated <- d$vaccinated / d$population

summary(re.cases.cent <- plm(diff(covid_cases) ~ eigenvector_centrality
                        + aggregate_inbound_cases
                        + vaccinated + ts, 
                        index=c("state", "ts"), data=d, model="random"))

Box.test(re.cases.cent$residuals)

plot(d$population ~ d$eigenvector_centrality)
