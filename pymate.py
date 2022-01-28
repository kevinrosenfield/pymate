import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class male:

    def __init__(self, m, g, gene=1.0):

        self.id = m
        self.group_id = g
        self.quality = np.random.uniform(1.0, 2.0)
        self.competitive_effort = gene
        self.gene = gene
        self.cost = self.quality**self.competitive_effort
        self.rank = "N/A"


class female:

    def __init__(self,
                 f,
                 days_until_cycling,
                 conception_probability_list,
                 mean_days_to_conception,
                 sd_days_to_conception,
                 g,
                 gene=1.0):

        self.id = f
        self.group_id = g
        self.days_until_cycling = days_until_cycling
        self.conception_probability_list = conception_probability_list
        self.conception_probability = "N/A"
        self.status = "not yet cycling"
        self.cycle_day = "N/A"
        self.gene = gene

        self.days_until_conception = abs(
            round(
                np.random.normal(mean_days_to_conception,
                                 sd_days_to_conception)))

    def switch_to_cycling(self, not_yet_cycling, females_cycling):

        females_cycling.append(self)
        not_yet_cycling.remove(self)
        self.status = "cycling"
        self.days_until_cycling = "N/A"

        self.cycle_day = 0
        self.conception_probability = self.conception_probability_list[
            0]  # starts day 0

    def switch_to_finished_cycling(self, females_cycling, finished_cycling):

        finished_cycling.append(self)
        females_cycling.remove(self)
        self.status = "finished cycling"
        self.cycle_day = "N/A"

        self.conception_probability = "N/A"


class group:

    # when a 'group' object is initialized, 'male' and 'female' objects are automatically instantiated in lists
    # ('males' and 'females') contained in the 'group' object
    # the male dominance hierarchy is set when the 'setRanks' method runs during 'group' initialization

    def __init__(self, g, array_of_latencies_to_cycling, conception_probability_list,
                 mean_days_to_conception, sd_days_to_conception):

        self.id = g
        self.females_not_yet_cycling = [
            female(f,
                   array_of_latencies_to_cycling[f],
                   conception_probability_list,
                   mean_days_to_conception,
                   sd_days_to_conception,
                   g=self.id) for f in range(number_females)
        ]

        self.females_cycling = []
        self.females_finished_cycling = []

        self.males = [male(m, g=self.id) for m in range(number_males)]

        self.mating_matrix = np.array(
            [np.array([1e-40] * number_males) for f in range(number_females)])

        self.list_of_rank_quality_corrlations = []

        self.set_ranks()
        
    def set_ranks(self):

        self.rank_entries = [m.quality**m.competitive_effort + 1e-50 for m in self.males]

        self.rank_entries_scaled = [
            e / sum(self.rank_entries) for e in self.rank_entries
        ]

        self.ranks = np.random.choice(range(number_males),
                                      p=self.rank_entries_scaled,
                                      size=number_males,
                                      replace=False)

        for i, m in enumerate(self.males):
            m.id = np.where(self.ranks == i)[0][0]
            m.rank = m.id

        self.list_of_rank_quality_corrlations.append(np.corrcoef([m.rank for m in self.males], [m.quality for m in self.males])[1, 0])

    def start_cycling(self):

        switch_to_cycling_list = []

        for f in self.females_not_yet_cycling:
            f.days_until_cycling -= 1
            if f.days_until_cycling < 0:
                switch_to_cycling_list.append(f)

        [
            f.switch_to_cycling(self.females_not_yet_cycling,
                                self.females_cycling)
            for f in switch_to_cycling_list
        ]

    def end_cycling(self, switch_to_finished_cycling_list):

        [
            f.switch_to_finished_cycling(self.females_cycling,
                                         self.females_finished_cycling)
            for f in switch_to_finished_cycling_list
        ]

    def make_mating_pairs(self):

        for m, f in enumerate(np.random.permutation(
                self.females_cycling)):  #randomize cycling females
            self.mating_matrix[
                f.id][m] += f.conception_probability * (self.males[m].quality - (self.males[m].competitive_effort/10))

    def go_one_day(self):

        self.start_cycling()

        switch_to_finished_cycling_list = []
        for f in self.females_cycling:
            f.days_until_conception -= 1
            if f.days_until_conception < 0:
                switch_to_finished_cycling_list.append(f)
            else:
                f.cycle_day = f.cycle_day + 1 if f.cycle_day < cycle_length - 1 else 0
                f.conception_probability = f.conception_probability_list[
                    f.cycle_day]

        self.end_cycling(switch_to_finished_cycling_list)

        self.make_mating_pairs() if any(
            [f.conception_probability for f in self.females_cycling]
        ) else 0  # only run function to make mating pairs if conception is possible

    def go_one_mating_season(self):

        self.set_ranks()
        self.males = sorted(self.males, key=self.sort_by_id)

        while len(self.females_finished_cycling) < number_females:
            self.go_one_day()

    def determine_next_gen_parents(self):

        self.females_finished_cycling = sorted(self.females_finished_cycling,
                                               key=self.sort_by_id)

        total_conception_probabilities = []
        self.parents = []

        for f in range(number_females):
            self.mating_matrix[f] = [
                fms / sum(self.mating_matrix[f])
                for fms in self.mating_matrix[f]
            ]

        for _ in [0, 1]:
            for mother in self.females_finished_cycling:

                #potential_fathers = random.choices(self.males, weights=[1 - m.cost for m in self.males] k=3)
                potential_fathers = random.choices(self.males, k=3)

                father = random.choices(potential_fathers,
                                        weights=self.mating_matrix[mother.id][[
                                            p.id for p in potential_fathers
                                        ]],
                                        k=1)[0]

                self.parents.append([mother, father])

    def generate_offspring(self, max_non_cycling_days,
                           conception_probability_list,
                           mean_days_to_conception, sd_days_to_conception):

        self.females_not_yet_cycling = []
        self.males = []

        self.parents = np.random.permutation(
            self.parents)  # randomize order to avoid biasing offspring sex

        for i, p in enumerate(
                self.parents[:number_females]
        ):  # loop through parents until reaching number females
            new_gene = np.random.choice([p[0].gene, p[1].gene])
            self.females_not_yet_cycling.append(
                female(i,
                       max_non_cycling_days,
                       conception_probability_list,
                       mean_days_to_conception,
                       sd_days_to_conception,
                       g=self.id,
                       gene=new_gene))

        for i, p in enumerate(
                self.parents[number_males:]
        ):  # loop through remaining parents until reaching number males
            new_gene = np.random.choice([p[0].gene, p[1].gene])
            self.males.append(male(i, g=self.id, gene=new_gene))

    def reset(self):

        self.females_finished_cycling = []

        self.mating_matrix = np.array(
            [np.array([1e-40] * number_males) for f in range(number_females)])

    def mutate(self):

        mutation_lottery = np.random.uniform(0, 1,
                                             number_males + number_females)

        number_mutations = sum(
            [1 for m in mutation_lottery if m < mutation_rate])

        for m in range(number_mutations):
            agent_mutating = random.choice(self.males +
                                           self.females_not_yet_cycling)
            agent_mutating.gene += np.random.uniform(-0.05, 0.05)
            if agent_mutating.gene < 1:# or agent_mutating.gene > 20:
                #agent_mutating.gene = round(agent_mutating.gene)
                agent_mutating.gene = 1

    def recombination(self):

        pass

    def make_agent_data_dfs(self):
        all_females = np.concatenate([
            np.array(self.females_not_yet_cycling),
            np.array(self.females_cycling),
            np.array(self.females_finished_cycling)
        ])

        self.female_data = pd.DataFrame({
            'id': [f.id for f in all_females],
            'status': [f.status for f in all_females],
            'days until cycling': [f.days_until_cycling for f in all_females],
            'days until conception':
            [f.days_until_conception for f in all_females],
            'conception probability':
            [f.conception_probability for f in all_females],
            'fertile mating success':
            [round(np.sum(i), 2) for i in self.mating_matrix]
        })

        self.male_data = pd.DataFrame({
            'rank': [f.rank for f in self.males],
            'competitive effort': [f.competitive_effort for f in self.males],
            'quality': [f.quality for f in self.males],
            'fertile mating success':
            [round(np.sum(i), 2) for i in self.mating_matrix.T]
        })

    def make_mating_df(self):
        self.mating_df = pd.DataFrame(self.mating_matrix).round(2).set_axis(
            ['m{}'.format(m) for m in range(number_males)],
            axis=1,
            inplace=False).set_axis(
                ['f{}'.format(f) for f in range(number_females)],
                axis=0,
                inplace=False)

    def plot_fertile_mating_success(self):
        self.make_mating_df()
        plt.figure(figsize=(14, 5))
        fig = sns.heatmap(self.mating_df, cmap='RdYlGn_r')

        means = np.array([round(np.mean(i),4) for i in self.mating_matrix.T])
        plt.rc('axes', labelsize=11.5)
        fig2 = plt.figure(figsize=(14, 5))
        myPlot = fig2.add_subplot(111)
        hm = myPlot.imshow(means[np.newaxis, :], cmap="RdYlGn_r", aspect="auto")
        plt.colorbar(hm)
        plt.yticks([])
        plt.xticks([])
        plt.xlabel('Male')
        plt.ylabel('Mean male conception probability\n across females')
        return fig2

    def sort_by_id(self, agent):
        return agent.id


class population:

    def __init__(self):

        pre = ovulation - 6
        post = cycle_length - pre - 6

        self.array_of_latencies_to_cycling = np.array([random.randint(0,round(365 - (365 * seasonality))) for i in range(number_females)])

        self.array_of_latencies_to_cycling -= (min(self.array_of_latencies_to_cycling) + 1)

        self.max_non_cycling_days = round(365 - (365 * seasonality))

        self.conception_probability_list = [0] * pre + [
            .05784435, .16082819, .19820558, .25408223, .24362408, .10373275
        ] + [0] * post

        self.mean_days_to_conception = 50
        self.sd_days_to_conception = 0  # * (1.0 - seasonality)

        self.groups = [
            group(g, self.array_of_latencies_to_cycling,
                  self.conception_probability_list,
                  self.mean_days_to_conception, self.sd_days_to_conception)
            for g in range(number_groups)
        ]

    def migrate(self):

        migration_lottery = np.random.uniform(
            0, 1, (number_males + number_females) * number_groups)

        number_migrations = sum(
            [1 for m in migration_lottery if m < migration_rate])

        number_females_migrating = random.randint(0, number_migrations)
        number_males_migrating = number_migrations - number_females_migrating

        self.groups_leaving = np.random.choice(self.groups,
                                               size=number_migrations)
        self.groups_coming = [
            random.choice([i for i in self.groups if i != l])
            for l in self.groups_leaving
        ]

        for gl, gc in zip(self.groups_leaving[:number_females_migrating],
                          self.groups_coming[:number_females_migrating]):

            fl = np.random.choice(gl.females_not_yet_cycling)
            fc = np.random.choice(gc.females_not_yet_cycling)

            gl.females_not_yet_cycling.remove(fl)
            gc.females_not_yet_cycling.remove(fc)

            gl.females_not_yet_cycling.append(fc)
            gc.females_not_yet_cycling.append(fl)

            fc.group_id = gl.id
            fl.group_id = gc.id

        for gl, gc in zip(self.groups_leaving[number_females_migrating:],
                          self.groups_coming[number_females_migrating:]):

            ml = np.random.choice(gl.males)
            mc = np.random.choice(gc.males)

            gl.males.remove(ml)
            gc.males.remove(mc)

            gl.males.append(mc)
            gc.males.append(ml)

            mc.group_id = gl.id
            ml.group_id = gc.id

    def evolve(self):
        for _ in range(number_generations):
            for g in self.groups:
                g.go_one_mating_season()
                g.determine_next_gen_parents()
                g.generate_offspring(self.max_non_cycling_days,
                                     self.conception_probability_list,
                                     self.mean_days_to_conception,
                                     self.sd_days_to_conception)
                g.reset()
                g.mutate()

            self.migrate()
            print(_) if np.random.uniform(0, 1) > 0.9 else 0

        for g in self.groups:
            g.set_ranks()
            g.males = sorted(g.males, key=g.sort_by_id)

        print([m.gene for m in self.groups[0].males])

model = []
number_generations = 100
number_groups = 3
number_females = 10
number_males = 10
seasonality = 0.0

mutation_rate = 0.01
migration_rate = 0.01
cycle_length = 28
ovulation = 16
pre = ovulation - 6
post = cycle_length - pre - 6

real_time_plots = False
