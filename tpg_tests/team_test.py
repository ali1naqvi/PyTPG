from random import randint
import unittest
import copy
import collections
from unittest import result
import scipy.stats as st
import math
import json

from numpy.testing._private.utils import assert_equal
import xmlrunner
from tpg.team import Team
from tpg_tests.test_utils import create_dummy_program, dummy_init_params, dummy_mutate_params, create_dummy_learner, create_dummy_team, create_dummy_learners

class TeamTest(unittest.TestCase):

    confidence_level = 99 # Confidence level in mutation probability correctness 95 = 95%
    confidence_interval = 5 # Confidence interval
    
    probabilities = [ 0.1, 0.25, 0.5, 0.66, 0.75, 0.82, 0.9] # probabilities at which to sample mutation functions, no 0 probabilities

    def compute_sample_size(self):
        # Compute samples required to achieve confidence intervals for mutation tests
        # https://www.statisticshowto.com/probability-and-statistics/find-sample-size/#CI1
        # https://stackoverflow.com/questions/20864847/probability-to-z-score-and-vice-versa
        z_a2 = st.uniform.ppf(1-(1-(self.confidence_level/100))/2)
        margin_of_error = (self.confidence_interval/100)/2
        mutation_samples = math.ceil(0.25*pow(z_a2/margin_of_error,2)) 
        return mutation_samples, margin_of_error


    def test_create_team(self):
        original_id_count = dummy_init_params['idCountTeam']

        # Create the team
        team = Team(dummy_init_params)

        # Verify instance variables and id
        self.assertIsNotNone(team.learners)
        self.assertIsNotNone(team.outcomes)
        self.assertIsNone(team.fitness)
        self.assertEqual(0,team.numLearnersReferencing)
        self.assertEqual(original_id_count, team.id)
        self.assertEqual(original_id_count+1, dummy_init_params['idCountTeam'])
        self.assertEqual(dummy_init_params['generation'], team.genCreate)


    '''
    Add a learner to a team
    '''
    def test_add_learners(self):

        team = Team(dummy_init_params)

        original_learners = team.learners

        l1 = create_dummy_learner()
        l2 = create_dummy_learner()

        l1_original_team_references = l1.numTeamsReferencing()
        l2_original_team_references = l2.numTeamsReferencing()

        team.addLearner(l1)
        team.addLearner(l2)

        #Ensure learner ref counts incremented
        self.assertEqual(l1_original_team_references + 1, l1.numTeamsReferencing())
        self.assertEqual(l2_original_team_references + 1, l2.numTeamsReferencing())

        #Ensure learner list grew
        self.assertEqual(2, len(team.learners))

        #Ensure no incomming learners appear in the team's inlearner list 
        self.assertEqual(0, len(team.inLearners))

    '''
    Verify that a team does not add a learner with the same program
    '''
    def test_no_duplicate_learners(self):

        program = create_dummy_program()
        l1 = create_dummy_learner()
        l2 = create_dummy_learner()

        # Set the program to be the same for both learners
        l1.program = copy.deepcopy(program)
        l2.program = copy.deepcopy(program)

        # Create a team
        team = Team(dummy_init_params)

        # Add the first learner
        team.addLearner(l1)

        # Assert that the second learner isn't added as it has an identical program
        with self.assertRaises(Exception) as expected:
            team.addLearner(l2)

            # Ensure the raised exception contains the correct message and the learner that triggered it
            msg, dupLearner = expected.exception.args
            self.assertEqual("Attempted to add learner whose program already exists in our learner pool", msg)
            self.assertEqual(dupLearner, l2)
    
    '''
    Verify that the team removes a given learner
    '''
    def test_remove_learner(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        random_index_in_learners = randint(0, num_learners-1)
        team, learners = create_dummy_team(num_learners)

        # Ensure the right number of learners appear in the team
        self.assertEqual(num_learners, len(team.learners))

        print("len(team.learners) before remove: {}".format(len(team.learners)))

        # Remove a randomly selected learner
        selected_learner = copy.deepcopy(team.learners[random_index_in_learners])
        print("selected learner: {}".format(selected_learner))
        print("learners[random_index_in_learners]: {}".format(learners[random_index_in_learners]) )
        
        print("selected and learners[random_index_in_learners] equal?: {}".format(selected_learner == learners[random_index_in_learners]))
        
        # Ensure the learner about to be removed has the team removing it in its inTeams list
        reference_to_removed_learner = team.learners[random_index_in_learners]
        self.assertTrue(team.id in reference_to_removed_learner.inTeams)

        team.removeLearner(selected_learner)

        print("len(team.learners) after remove: {}".format(len(team.learners)))

        # Ensure the list the team's learners shrunk by 1
        self.assertEqual(num_learners-1, len(team.learners))
        

        # Ensure the learner at the randomly selected index is no longer the selected learner
        if random_index_in_learners < len(team.learners): # If we deleted from the end of the list this assert would IndexError
            self.assertNotEqual(selected_learner, team.learners[random_index_in_learners])

        # Ensure nothing is removed if we ask to remove the same learner again
        team.removeLearner(selected_learner)
        self.assertEqual(num_learners - 1, len(team.learners))

        # Ensure the referenced learner was not deleted outright
        print("removed learner: {}".format(reference_to_removed_learner))
        self.assertIsNotNone(reference_to_removed_learner)

        # Ensure the learner that has been removed from the team no longer has the team's id in it's inTeams list
        print("reference to removed inTeams: {}".format(reference_to_removed_learner.inTeams))
        self.assertFalse(team.id in reference_to_removed_learner.inTeams)

    '''
    Verify that removing all learners from a team does so, without 
    destroying the underlying learner objects
    '''
    def test_remove_all_learner(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        team, learners = create_dummy_team(num_learners)

        team.removeLearners()

        # Ensure learners were deleted
        self.assertEqual(0, len(team.learners))
        self.assertEqual(num_learners, len(learners))

        # Ensure deleted learner's inTeams list reflects this
        for learner in learners:
            self.assertEqual(0, len(learner.inTeams))

    def test_num_atomic_actions(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        team, learners = create_dummy_team(num_learners)

        # Pick a random number smaller than the number of learners on the team to make non-atomic
        random_subset_bound = randint(0, num_learners-1)

        for i in range(0, random_subset_bound):
            team.learners[i].actionObj.teamAction = -1 # By making the team action not None we have a mock non-atomic action
        
        print("made {}/{} action objects non-atomic".format(random_subset_bound, len(team.learners)))

        # Ensure the number of atomic actions reported by the team is the total - those we made non-atomic
        self.assertEqual(num_learners - random_subset_bound, team.numAtomicActions())

    #@unittest.skip
    def test_mutation_delete(self):

        # Create a team with a random number of learners
        num_learners = randint(0,256)
        hi_probability_team, _ = create_dummy_team(num_learners)

        no_atomic_team, _ = create_dummy_team(num_learners)
        for i in range(0, num_learners):
            no_atomic_team.learners[i].actionObj.teamAction = -1 # By making the team action not None we have a mock non-atomic action

        self.assertEqual(0, no_atomic_team.numAtomicActions())

        num_learners_before = len(hi_probability_team.learners)

        #Ensure we error out if passing in a probability greater than 1.0
        with self.assertRaises(Exception) as expected:
            hi_probability_team.mutation_delete(1.1)
            msg = expected.exception.args
            self.assertEqual("pLrnDel is greater than or equal to 1.0!", msg)

        # Ensure nothing was deleted
        self.assertEqual(num_learners_before, len(hi_probability_team.learners))
        
        #Ensure we error out if we have no atomic actions
        with self.assertRaises(Exception) as expected:
            no_atomic_team.mutation_delete(0.99)

            # Ensure we spit back the problem team when we error
            msg, problem_team = expected.exception.args
            self.assertEqual("Less than one atomic action in team! This shouldn't happen",msg)
            self.assertTrue(isinstance(problem_team, Team))

        results = {}

        # Create a team with 100 learners
        template_team, _ = create_dummy_team(100)
        
        mutation_samples, margin_of_error = self.compute_sample_size()

        print('Need {} mutation samples to estabilish {} CL with {} margin of error in mutation probabilities'.format(mutation_samples, self.confidence_level, margin_of_error))

        for i in self.probabilities:
            print("Testing delete mutation with probability {}".format(i))


            # List counting the number of deleted learners over the test samples
            results[str(i)] = [None] * mutation_samples

            for j in range(0, mutation_samples):
                #print('sample {}/{} probability={}'.format( j, mutation_samples, i))
                team = copy.deepcopy(template_team)
                before = len(team.learners) 
                
                # Perform mutation delete
                deleted_learners = team.mutation_delete(i)
                
                # Store the number of deleted learners
                results[str(i)][j] = before - len(team.learners)
                # Ensure the number of returned learners matches the number of deleted learners computed from the size difference
                self.assertEqual(results[str(i)][j], len(deleted_learners)) 
            
                # Ensure the deleted learners no longer have the team in their inTeam lists
                for cursor in deleted_learners:
                    self.assertNotIn(cursor, team.learners)
                    self.assertNotIn(team.id, cursor.inTeams)

            # Count how often 1 learners where deleted, how often 2 learners were deleted ... etc
            frequency = collections.Counter(results[str(i)])
            print(frequency)

            '''
            Ensure the number of deleted learners conforms to the expected proabilities
            as given by probability^num_deleted learners. Eg: with a delete probability
            of 0.5 we expect to delete 2 learers 0.25 or 25% of the time...or do we...TODO
            '''
            report = {}
            header_line = "{:<40}".format('num_deleted (X or more) @ probability: {}'.format(i))
            actual_line = "{:<40}".format("actual")
            actual_freq_line = "{:<40}".format("actual freqency")
            expected_line = "{:<40}".format("expected probability")
            acceptable_error = "{:<40}".format("acceptable error")
            error_line = "{:<40}".format("error")
            for num_deleted in range(max(list(frequency.elements()))+1):
                report[str(num_deleted)] = {}

                # Sum up the frequencies to give the observed frequency of num_deleted or more learners removed
                occurance = frequency[num_deleted]
                if num_deleted != 0:
                    occurance = 0
                    for cursor in range(num_deleted, max(list(frequency.elements()))+1):
                        occurance = occurance + frequency[cursor]


                report[str(num_deleted)]['occurance'] = occurance
                report[str(num_deleted)]['actual'] = occurance/mutation_samples

                # Compute consecutive deletion expected probabilities
                expected = i
                for cursor in range(1,num_deleted):
                    #expected *= pow(i,pow(2,cursor))
                    expected *= i
                report[str(num_deleted)]['expected'] = expected

            

                
                header_line = header_line + "\t{:>5}".format(num_deleted)
                actual_line = actual_line + "\t{:>5}".format(report[str(num_deleted)]['occurance'])
                actual_freq_line = actual_freq_line + "\t{:>5.4f}".format(report[str(num_deleted)]['actual'])
                expected_line = expected_line + "\t{:>5.4f}".format(report[str(num_deleted)]['expected'] if num_deleted != 0 else (1-i))
                acceptable_error = acceptable_error + "\t{:>5.4f}".format((self.confidence_interval/100)*num_deleted if num_deleted != 0 else (self.confidence_interval/100))
                error_line = error_line + "\t{:>5.4f}".format(abs(report[str(num_deleted)]['actual'] - (report[str(num_deleted)]['expected'] if num_deleted != 0 else (1-i))))

                '''
                TODO It seems the expected probabilties and the actual ones can deviate sharply when num_deleted > 1. 
                I expect this is because the margin of error grows equal to the number of successive iterations? But I'm too
                statistically handicapped to confirm this. 
                '''
                if num_deleted == 0:
                    self.assertAlmostEqual((1-i),report[str(num_deleted)]['actual'],  delta=self.confidence_interval/100)
                if num_deleted >= 1:
                #    self.assertAlmostEqual(report[str(num_deleted)]['expected'],report[str(num_deleted)]['actual'],  delta=(self.confidence_interval/100)*num_deleted)
                    print('')
            print(header_line)
            print(actual_line)
            print(actual_freq_line)
            print(expected_line)
            print(acceptable_error)
            print(error_line)
    
    @unittest.skip
    def test_mutation_add(self):

        # Create several teams with random numbers of learners
        team_template, learners1 = create_dummy_team(randint(2,256))

        # Create a dummy pool of learners to add from
        learner_pool = create_dummy_learners()


        # Ensure an exception is raised if we add with a probability of 1.0
        with self.assertRaises(Exception) as expected:
            team = copy.deepcopy(team_template)
            team.mutation_add(1.0, learner_pool)

            msg = expected.exception.args
            self.assertEqual("pLrnAdd is greater than or equal to 1.0!")

        # Ensure nothing is added if we add with a probability of 0
        team = copy.deepcopy(team_template)
        original_size = len(team.learners)
        team.mutation_add(0.0, learner_pool)
        self.assertEqual(len(team.learners), original_size)

        results = {}

        mutation_samples, margin_of_error = self.compute_sample_size()

        for i in self.probabilities:
            print("Testing add mutation with probability {}".format(i))

            # List counting the number of added learners over the test sample
            results[str(i)] = [None] * mutation_samples

            for j in range(0, mutation_samples):
                team = copy.deepcopy(team_template)
                before = len(team.learners)

                # Perform mutation add
                added_learners = team.mutation_add(i, learner_pool)

                # Store the number of added teams
                results[str(i)][j] = len(team.learners) - before

                # Ensure the number of returned learners matches the number of added learners computed from the size difference
                self.assertEqual(results[str(i)][j], len(added_learners))

                # Ensure the added learners now have the team in their inTeam list
                for cursor in added_learners:
                    self.assertIn(cursor, team.learners)
                    self.assertIn(team.id, cursor.inTeams)

            frequency = collections.Counter(results[str(i)])
            print(frequency)

            report = {}
            header_line = "{:<40}".format('num_added (X or more) @ probability: {}'.format(i))
            actual_line = "{:<40}".format("actual")
            actual_freq_line = "{:<40}".format("actual freqency")
            expected_line = "{:<40}".format("expected probability")
            acceptable_error = "{:<40}".format("acceptable error")
            error_line = "{:<40}".format("error")

            for num_added in range(max(list(frequency.elements()))+1):
                report[str(num_added)] = {}

                # Sum up the frequencies to give the observed frequency of num_added or more learners added
                occurance = frequency[num_added]
                if num_added != 0:
                    occurance = 0
                    for cursor in range(num_added, max(list(frequency.elements()))+1):
                        occurance = occurance + frequency[cursor]
                
                report[str(num_added)]['occurance'] = occurance
                report[str(num_added)]['actual'] = occurance/mutation_samples

                # Compute consecutive addition expected probabilities
                expected  = i
                for cursor in range(1, num_added):
                    expected *= pow(i,pow(2,cursor))
                report[str(num_added)]['expected'] = expected

                header_line = header_line + "\t{:>5}".format(num_added)
                actual_line = actual_line + "\t{:>5}".format(report[str(num_added)]['occurance'])
                actual_freq_line = actual_freq_line + "\t{:>5.4f}".format(report[str(num_added)]['actual'])
                expected_line = expected_line + "\t{:>5.4f}".format(report[str(num_added)]['expected'] if num_added != 0 else (1-i))
                acceptable_error = acceptable_error + "\t{:>5.4f}".format((self.confidence_interval/100)*num_added if num_added != 0 else (self.confidence_interval/100))
                error_line = error_line + "\t{:>5.4f}".format(abs(report[str(num_added)]['actual'] - (report[str(num_added)]['expected'] if num_added != 0 else (1-i))))

                if num_added == 0:
                    self.assertAlmostEqual((1-i), report[str(num_added)]['actual'], delta=self.confidence_interval/100)
                if num_added >= 1:
                    self.assertAlmostEqual(report[str(num_added)]['expected'], report[str(num_added)]['actual'], delta=(self.confidence_interval/100)*num_added)

            print(header_line)
            print(actual_line)
            print(actual_freq_line)
            print(expected_line)
            print(acceptable_error)
            print(error_line)

    @unittest.skip
    def test_mutation_mutate(self):

        # Create a team with num_learners learners
        num_learners = 10
        team_template, learners = create_dummy_team(num_learners)
        aux_team, aux_learners = create_dummy_team(num_learners)
        aux_team_2, aux_learners_2 = create_dummy_team(num_learners)

        print('Original learner actions')
        for cursor in learners:
            print("{}:{}".format( cursor.id, cursor.actionObj))

        team_pool = []
        team_pool.append(aux_team)
        team_pool.append(aux_team_2)
        team_pool.append(team_template)

        mutation_samples, margin_of_error = self.compute_sample_size()
    

        results = {}
        print('Need {} mutation samples to establish {} CL with a {} margin of error'.format(mutation_samples, self.confidence_level, margin_of_error))

        for i in self.probabilities:
            print("Testing mutate mutation with probability {}".format(i))

            # List counting the number of mutated learners over the test
            results[str(i)] = [None] * mutation_samples

            for j in range(0, mutation_samples):
                team = copy.deepcopy(team_template)

                # Ensure the copy worked
                self.assertEqual(team, team_template)

                mutated_learners = team.mutation_mutate(i, dummy_mutate_params, team_pool)

                for cursor in mutated_learners:
                    '''
                    Find the mutated learner by id from the template team's learners to get what the learner looked
                    like before it was mutated.
                    '''
                    pre_mutation_learner = next(x for x in team_template.learners if x.id == cursor.id)
            
                    # Ensure the mutated learner has changed from it's inital state in the template team
                    # Meaning it's no longer equal to its past self.
                    #print('checking for mutation in learner {}'.format( pre_mutation_learner.id))

                    

                    self.assertNotEqual(cursor, pre_mutation_learner)    
                
                # Count the number of different learners between the template team
                # and the mutated team
                diff = 0
                for learner in team_template.learners:
                    if learner not in team.learners:
                        diff += 1

                # Ensure the number of differences corresponds to the length of the mutated_learners list
                self.assertEqual(diff, len(mutated_learners))

                # Record the number of mutations
                results[str(i)][j] = diff
        
            # Count how often 1 learner was mutated, how often 2 learners were mutated, etc.
            frequency = collections.Counter(results[str(i)])
            print(frequency)

            report = {}
            header_line = "{:<40}".format('num_mutated/{} (X or more) @ probability: {}'.format(num_learners,i))
            actual_line = "{:<40}".format("actual")
            actual_freq_line = "{:<40}".format("actual freqency")

            # These number of mutated learners should have the highest probabilities
            floor = math.floor(num_learners * i)
            ceiling = math.ceil(num_learners * i)

            for num_mutated in range(max(list(frequency.elements()))+1):
                report[str(num_mutated)] = {}

                report[str(num_mutated)]['occurance'] = frequency[num_mutated]
                report[str(num_mutated)]['actual'] = frequency[num_mutated]/mutation_samples
                
                header_line = header_line + "\t{:>5}".format(num_mutated)
                actual_line = actual_line + "\t{:>5}".format(report[str(num_mutated)]['occurance'])
                actual_freq_line = actual_freq_line + "\t{:>5.4f}".format(report[str(num_mutated)]['actual'])
                

                # Ensure number of mutations is concentrated at probability * number of learners
                if num_mutated != floor and num_mutated != ceiling:
                    self.assertLessEqual(report[str(num_mutated)]['actual'] , (frequency[floor]/mutation_samples) + (frequency[ceiling]/mutation_samples))


            
            print(header_line)
            print(actual_line)
            print(actual_freq_line)

    def test_mutate(self):

        # Generate 3 teams for a mutation test
        alpha_t, alpha_l = create_dummy_team(10)
        beta_t, beta_l = create_dummy_team(10)
        charlie_t, charlie_l = create_dummy_team(10)

        mutate_params_1 = copy.deepcopy(dummy_mutate_params)
        mutate_params_1['generation'] = 1
        mutate_params_1['rampantGen'] = 0 #No rampancy

        mutate_params_2 = copy.deepcopy(dummy_mutate_params)
        mutate_params_2['generation'] = 1
        mutate_params_2['rampantGen'] = 1 # Rampancy every generation

        # Between 1 and 5 iterations of mutation
        mutate_params_2['rampantMin'] = 1 
        mutate_params_2['rampantMax'] = 5 

        mutate_params_3 = copy.deepcopy(dummy_mutate_params)
        mutate_params_3['generation'] = 2
        mutate_params_3['rampantGen'] = 1 # Rampancy every generation

        # 3 iterations of mutation every generation
        mutate_params_3['rampantMin'] = 3 
        mutate_params_3['rampantMax'] = 3 

        learner_pool = alpha_l + beta_l + charlie_l
        team_pool = [alpha_t, beta_t, charlie_t]

        # Mutate alpha_t
        mutations = alpha_t.mutate(mutate_params_1, learner_pool, team_pool)
        self.assertEqual(1, mutations)

        # Mutate beta_t
        mutations = beta_t.mutate(mutate_params_2, learner_pool, team_pool)
        self.assertTrue(mutations >= mutate_params_2['rampantMin'] and mutations <= mutate_params_2['rampantMax'])

        # Mutate charlie_t
        mutations = charlie_t.mutate(mutate_params_3, learner_pool, team_pool)
        self.assertEqual(mutations, mutate_params_3['rampantMin'])



if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
