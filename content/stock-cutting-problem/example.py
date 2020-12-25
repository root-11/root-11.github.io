from math import ceil
# The [stock cutting problem](https://en.wikipedia.org/wiki/Cutting_stock_problem) is defined as:
# the problem of cutting standard-sized pieces of stock material, such
# as paper rolls or sheet metal, into pieces of specified sizes while
# minimizing material wasted.
# It is an optimization problem in mathematics that arises from applications in industry.


def example_1():
    # user inputs
    item_sizes = [1800, 1100, 1060, 760, 740]
    BOM = [4, 4, 4, 4, 4]  # Bill Of Materials
    material_lengths = [2500, 5000]
    print("lower bound:", lower_bound(item_sizes, BOM, material_lengths))
    solution = greedy_tournament(item_sizes, BOM, material_lengths)
    print(solution)


# The best possible solution is the lower bound, given by:
def lower_bound(item_sizes, item_quantities, material_lengths):
    return ceil(sum(a*b for a,b in zip(item_sizes, item_quantities)) / min(material_lengths)) * min(material_lengths)


# We define quality of a certain sequence of cuts on the standard material,
# as the amount of material wasted. We call the data structure for this a Cut:

class Cut(object):
    def __init__(self, material_length):
        self.material_length = self.remainder = material_length
        self.cuts = tuple()

    @property
    def waste(self):
        return self.material_length - sum(self.cuts)

    def greedy_select(self, list_of_materials):
        """ Selects materials from list of materials """
        for m in list_of_materials:
            if m <= self.remainder:
                self.remainder -= m
                self.cuts += (m,)

    def __lt__(self, other):
        return self.waste < other.waste

    def __str__(self):
        return f"{self.material_length}: {self.cuts} + {self.waste}"

# We add three helping functions to the cut:
# - greedy_select, which chooses cuts from a list of materials.
# - waste, as a property of the pieces selected minus the left over.
# - __lt__ which allows us to sort and compare waste between two solutions.


# We also define the collection of Cut's that fulfil all material requirements
# as a Plan. The quality of the Plan is determined by the total amount of material
# wasted.


class Plan(object):
    def __init__(self):
        self.cuts = []

    @property
    def waste(self):
        return sum(c.waste for c in self.cuts)

    @property
    def materials(self):
        return sum(c.material_length for c in self.cuts)

    def __str__(self):
        L = [f"total materials: {self.materials}, total waste: {self.waste}"]
        return "\n".join(L + [f"({i}) {c}" for i,c in enumerate(self.cuts)])


def greedy_tournament(item_sizes, item_quantities, material_lengths):
    list_of_materials = []
    for L, qty in zip(item_sizes, item_quantities):
        list_of_materials.extend([L] * qty)

    list_of_materials.sort(reverse=True)  # materials sorted descending.

    plan = Plan()
    while list_of_materials:
        candidate_materials = [m for m in material_lengths if m > max(list_of_materials)]
        if not candidate_materials:
            raise ValueError(f"no candidate materials for length: {max(list_of_materials)}")

        # simple competitive tournament between candidate materials.
        candidate_solutions = []
        for candidate_material in candidate_materials:
            cut = Cut(candidate_material)
            cut.greedy_select(list_of_materials)
            candidate_solutions.append(cut)
        candidate_solutions.sort()
        least_waste = candidate_solutions[0]

        plan.cuts.append(least_waste)  # retain the best solution.
        for cut in least_waste.cuts:  # remove the materials selected by the best solution.
            list_of_materials.remove(cut)

    return plan


example_1()
