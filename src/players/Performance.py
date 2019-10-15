class Performance:
    categories = {
        # counter , score multiplier, description
        'hakem_shelem': [0, 3,      'Is hakem and has shelemed'],
        'hakem_success': [0, 2,     'Is hakem and got the bid'],
        'hakem_fail': [0, -4,       'Is hakem but failed to get the bid'],
        'hakem_double': [0, -5,     'Is hakem but got doubled'],
        'not_hakem_success': [0, 2, 'Is opposite and hakem failed to got the bid'],
        'not_hakem_fail': [0, -2,    'Is opposite and hakem got the bid'],
        'not_hakem_shelem': [0, -3, 'Is opposite and has been shelemed'],
        'not_hakem_double': [0, 3,  'Is opposite and hakem has doubled']
    }

    def calculate_score(self):
        s = 0
        for item in self.categories:
            s += self.categories[item][0] * self.categories[item][1]
        return s

    def __str__(self):
        string = ['=================== Performance ====================']
        for item in self.categories:
            string.append(f'{self.categories[item][2]} -> {self.categories[item][0]}')
        string.append(f'weighted score: {self.calculate_score()}')
        return '\n'.join(string)

    def __getattr__(self, item):
        return self.categories[item][0]

    def increase(self, item):
        self.categories[item][0] += 1

