import random
from time import perf_counter

from core.neighbor import Neighbor
from core.state import State
from core.entity import Package
from util.stateHelper import StateHelper
from .result import GeneticAlgorithmResult

MAX_CROSSOVER_LIMIT = 1000

class GeneticAlgorithm:
    def __init__(self, nPopulation: int, nGeneration: int, seed: int):
        self.nPopulation = nPopulation
        self.nGeneration = nGeneration
        self.seed = seed
        self.rng = random.Random(seed)

        self.random_position_used = 0

    @staticmethod
    def _fitness_function(value: int, sumValue: int) -> int:
        return value*100.0/sumValue
    
    @staticmethod
    def _random_roulette(population: list[State], nPopulation: int, sumValue: int, rng) -> State:
        selectedState: State
        rr = rng.randint(0,100) #random pick

        for _ in range(nPopulation):
            f = GeneticAlgorithm._fitness_function(population[0].getValue(), sumValue) 
            if f >= rr:
                selectedState = population[0]
                return selectedState
            else:
                for i in range (1, nPopulation):
                    f += GeneticAlgorithm._fitness_function(population[i].getValue(), sumValue) 
                    if f >= rr:
                        selectedState = population[i]
                        return selectedState
                    
        return population[-1]

    def _mutate(self, state: State, mutation_point: int) -> State:
        package = state.packages[mutation_point]
        operations = ["move", "rotate"]
        if len(state.packages) > 1:
            operations.append("swap")

        operation = self.rng.choice(operations) #random mutation value
        if operation == "move":
            for _ in range(100):
                new_position = StateHelper.randomize(state.getDimOri(package), state.truck.dimPeti, self.rng)
                candidate = Neighbor.move(state, package.id, new_position)
                if candidate is not None: return candidate
        elif operation == "rotate":
            for axis in self.rng.sample(("x", "y", "z"), 3):
                candidate = Neighbor.rotate(state, package.id, axis)
                if candidate is not None: return candidate
        else:
            partners: list[Package] = []
            for other in state.packages:
                if other.id == package.id: continue
                partners.append(other)
            
            self.rng.shuffle(partners)
            for partner in partners:
                candidate = Neighbor.swap(state, package.id, partner.id)
                if candidate is not None: return candidate

        return state

    def _run_one_generation(self, population: list[State]) -> list[State]:

        countPackageIndividual = len(population[0].packages)
        truck = population[0].truck

        # fitness function
        sumValue = 0
        for p in population:
            sumValue += p.getValue()

        # 1. selection - random roulette, sekali jalan pick 2
        selectedStates: list[State] = []
        parent_pair_count = (self.nPopulation + 1) // 2 #tangani ganjil
        for _ in range(parent_pair_count):
            selectedState1 = self._random_roulette(population, self.nPopulation, sumValue, self.rng)
            selectedState2 = self._random_roulette(population, self.nPopulation, sumValue, self.rng)

            selectedStates.append(selectedState1)
            selectedStates.append(selectedState2)

       
        # 2. crossover, gabung state paket antar 2 parent secara package by package
        crossedState: list[State] = []
        self.crossover_limit_reached = False

        for i in range(0, len(selectedStates), 2):
            # selectedStates[i] <- ayah
            # selectedStates[i+1] <- ibu
            parent1: State = selectedStates[i]
            parent2: State = selectedStates[i+1]

            for _ in range(2):  # dari satu pasangan parent menghasilkan 2 child
                positions = {}
                crossedPackages: list[Package] = []
                crossover_attempts = 0

                # urutkan paket berdasarkan z terkecil dari kedua parent, meminimalkan floating
                packageOrder = list(parent1.packages)
                self.rng.shuffle(packageOrder)
                packageOrder.sort(
                    key=lambda p: min(
                        parent1.getPosition(p)[2],
                        parent2.getPosition(p)[2]
                    )
                )

                # tempatkan paket per paket
                for package in packageOrder:
                    placed = False

                    # coba posisi dari parent 1 dan parent 2
                    candidatePositions = [parent1.getPosition(package), parent2.getPosition(package)]
                    self.rng.shuffle(candidatePositions)

                    for candidatePosition in candidatePositions:
                        crossover_attempts += 1
                        if crossover_attempts >= MAX_CROSSOVER_LIMIT:
                            self.crossover_limit_reached = True
                            return population

                        if State.isValidPlacement(
                            package,
                            candidatePosition,
                            positions,
                            parent1.packages,
                            truck,
                            self.rng
                        ):
                            crossedPackages.append(package)
                            placed = True
                            break

                    # Kalau posisi kedua parent gagal, coba posisi random.
                    while not placed and crossover_attempts < MAX_CROSSOVER_LIMIT:
                        crossover_attempts += 1

                        newPosition = StateHelper.randomize(package.dim, truck.dimPeti, self.rng)

                        if State.isValidPlacement(
                            package,
                            newPosition,
                            positions,
                            parent1.packages,
                            truck,
                            self.rng
                        ):
                            crossedPackages.append(package)
                            placed = True
                            self.random_position_used += 1

                    if not placed:
                        self.crossover_limit_reached = True
                        return population

                # Semua paket sudah ditempatkan -> satu child
                crossedState.append(State(crossedPackages, truck, self.rng, False, positions))

        # 3. mutation
        mutation_point = self.rng.randint(0, countPackageIndividual-1)
        childStates: list[State] = []
        for st in crossedState:
            childStates.append(self._mutate(st, mutation_point))

        return childStates[:self.nPopulation]

    def run(self, initial_state: State):
        start_time = perf_counter()

        # initiate population
        population: list[State] = []
        for _ in range(self.nPopulation):
            state = State(initial_state.packages, initial_state.truck, self.rng)
            population.append(state)

        value_history: list[float] = []
        average_value_history: list[float] = []
        count_package_individual = len(population[0].packages)

        ## catat statistik populasi awal
        value_history.append(max(st.getValue() for st in population))
        average_value_history.append(sum(st.getValue() for st in population) / len(population))

        # jalanin GA untuk satu generasi: selection, crossover, mutation
        stop_reason = "max_iterations_reached"
        iterations = 0
        for _ in range(self.nGeneration):
            population = self._run_one_generation(population)
            if self.crossover_limit_reached:
                stop_reason = "max_crossover_limit"
                break

            iterations += 1
            value_history.append(max(st.getValue() for st in population))
            average_value_history.append(sum(st.getValue() for st in population) / len(population))


        # pilih state terbaik dari final population
        bestSoFar = -99
        finalState: State 
        for st in population:
            if bestSoFar < st.getValue(): 
                bestSoFar = st.getValue()
                finalState = st

        
        return GeneticAlgorithmResult(
            algorithm = "genetic_algorithm",
            initial_state = initial_state,
            final_state = finalState,
            accepted_moves = 0,
            iterations=iterations,
            value_history=value_history,
            average_value_history=average_value_history,
            duration_seconds=perf_counter()-start_time,
            stop_reason=stop_reason,
            parameters={
                "n_population": self.nPopulation,
                "n_generation": self.nGeneration,
                "seed": self.seed,
            },
            metadata={
                "best_value_seen": max(value_history),
                "count_package_individual": count_package_individual,
                "random_position_used": self.random_position_used,
                "random_position_rate": self.random_position_used/(self.nPopulation*count_package_individual*iterations)
            },
        )

        