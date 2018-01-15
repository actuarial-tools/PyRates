"""Templates for specific circuit parametrizations.
"""

import numpy as np

from core.circuit import CircuitFromPopulations, Circuit
from core.population import WangKnoescheCells
from core.population import MoranPyramidalCells, MoranExcitatoryInterneurons, MoranInhibitoryInterneurons
from core.population import JansenRitPyramidalCells, JansenRitInterneurons
from typing import Optional

__author__ = "Richard Gast, Daniel Rose"
__status__ = "Development"


#######################
# jansen-rit circuits #
#######################


class JansenRitCircuit(CircuitFromPopulations):
    """Basic Jansen-Rit circuit as defined in [1]_.

    Parameters
    ----------
    resting_potential
        Default = 0.0 V.
    step_size
        Default = 5e-4 s.
    max_synaptic_delay
        Default = None.
    delays
        Default = None
    init_states
        Default = np.zeros(3)

    See Also
    --------
    :class:`CircuitFromPopulations`: Detailed description of parameters.
    :class:`Circuit`: Detailed description of attributes and methods.

    References
    ----------
    .. [1] B.H. Jansen & V.G. Rit, "Electroencephalogram and visual evoked potential generation in a mathematical model
       of coupled cortical columns." Biological Cybernetics, vol. 73(4), pp. 357-366, 1995.

    """

    def __init__(self,
                 resting_potential: float = 0.0,
                 step_size: float = 5e-4,
                 max_synaptic_delay: Optional[float] = None,
                 delays: Optional[np.ndarray] = None,
                 init_states: np.ndarray=np.zeros(3),
                 ) -> None:
        """Initializes a basic Jansen-Rit circuit of pyramidal cells, excitatory interneurons and inhibitory
        interneurons.
        """

        # set parameters
        ################

        populations = ['JansenRitPyramidalCells',
                       'JansenRitInterneurons',
                       'JansenRitInterneurons']

        population_labels = ['JR_PCs',
                             'JR_EINs',
                             'JR_IINs']

        N = 3                                               # PCs, EINs, IIns
        n_synapses = 2                                      # excitatory and inhibitory

        # set connections
        #################

        connections = np.zeros((N, N, n_synapses))
        c = 135.

        # excitatory connections
        connections[:, :, 0] = [[0, 0.8 * c, 0],
                                [1.0 * c, 0, 0],
                                [0.25 * c, 0, 0]]

        # inhibitory connections
        connections[:, :, 1] = [[0, 0, 0.25 * c],
                                [0, 0, 0],
                                [0, 0, 0]]

        # call super init
        #################

        super().__init__(population_types=populations,
                         connectivity=connections,
                         delays=delays,
                         population_class='SecondOrderPopulation',
                         population_labels=population_labels,
                         resting_potential=resting_potential,
                         step_size=step_size,
                         max_synaptic_delay=max_synaptic_delay,
                         init_states=init_states)


class GeneralizedJansenRitCircuit(Circuit):
    """

    """
    def __init__(self,
                 n_circuits,
                 synapse_params=None,
                 axon_params=None,
                 connectivity_scalings=None,
                 weights=None,
                 step_size=5e-4,
                 max_synaptic_delay=0.2
                 ):
        """"""

        if not synapse_params:
            synapse_params = [None for i in range(n_circuits)]
        if not axon_params:
            axon_params = [None for i in range(n_circuits)]
        if not connectivity_scalings:
            connectivity_scalings = [135 for i in range(n_circuits)]
        if not weights:
            weights = [1/n_circuits for i in range(n_circuits)]

        connectivity = np.zeros((n_circuits * 3, n_circuits * 3, 2))
        conns = np.zeros((3, 3, 2))
        populations = list()

        for i in range(n_circuits):

            #if synapse_params[i]:
            #    scaling = (10. * synapse_params[i][1]['tau']) / (20. * synapse_params[i][0]['tau'])
            #    synapse_params[i][0]['efficacy'] = 3.25e-3 * scaling

            pcs = JansenRitPyramidalCells(synapse_params=synapse_params[i],
                                          axon_params=axon_params[i],
                                          step_size=step_size,
                                          max_synaptic_delay=max_synaptic_delay,
                                          label='JR_PCs_' + str(i))
            eins = JansenRitInterneurons(synapse_params=[synapse_params[i][0]],
                                         axon_params=axon_params[i],
                                         step_size=step_size,
                                         max_synaptic_delay=max_synaptic_delay,
                                         label='JR_EINs_' + str(i))
            iins = JansenRitInterneurons(synapse_params=[synapse_params[i][0]],
                                         axon_params=axon_params[i],
                                         step_size=step_size,
                                         max_synaptic_delay=max_synaptic_delay,
                                         label='JR_IINs_' + str(i))

            c = connectivity_scalings[i]
            # excitatory connections
            conns[:, :, 0] = [[0, 0.8 * c, 0],
                              [1.0 * c, 0, 0],
                              [0.25 * c, 0, 0]]

            # inhibitory connections
            conns[:, :, 1] = [[0, 0, 0.25 * c],
                              [0, 0, 0],
                              [0, 0, 0]]

            connectivity[:, i*3:(i+1)*3, :] = np.tile(weights[i] * conns, (n_circuits, 1, 1))
            populations += [pcs, eins, iins]

        super().__init__(populations=populations,
                         connectivity=connectivity,
                         delays=np.zeros((n_circuits * 3, n_circuits * 3)),
                         step_size=step_size)


#########################################################################
# wang knoesche circuit with synaptic plasticity on excitatory synapses #
#########################################################################


class WangKnoescheCircuit(Circuit):
    """Basic 5-population cortical column circuit as defined in [1]_.

    Parameters
    ----------
    step_size
        Default = 5e-4 s.
    max_synaptic_delay
        Default = None.
    delays
        Default = None
    init_states
        Default = np.zeros(5)
    tau_depression
        Default = 0.05 s.
    tau_recycle
        Default = 0.5 s.

    See Also
    --------
    :class:`CircuitFromPopulations`: Detailed description of parameters.
    :class:`Circuit`: Detailed description of attributes and methods.

    References
    ----------
    .. [1] P. Wang & T.R. Knoesche, "A realistic neural mass model of the cortex with laminar-specific connections and
       synaptic plasticity-evaluation with auditory habituation." PloS one, vol. 8(10): e77876, 2013.

    """

    def __init__(self,
                 step_size: float = 5e-4,
                 max_synaptic_delay: Optional[float] = None,
                 delays: Optional[np.ndarray] = None,
                 init_states: np.ndarray = np.zeros(5),
                 tau_depression: float = 0.05,
                 tau_recycle: float = 0.5
                 ) -> None:
        """Initializes a basic Wang-Knoesche circuit of pyramidal cells and inhibitory interneurons in layer 2/3 as well
        as layer 5/6 plus a layer 4 excitatory interneuron population.
        """

        # set parameters
        ################

        # synapse information
        n_synapses = 2

        # populations
        l23_pcs = WangKnoescheCells(step_size=step_size,
                                    max_synaptic_delay=max_synaptic_delay,
                                    init_state=init_states[0],
                                    label='L23_PCs',
                                    tau_depression=tau_depression,
                                    tau_recycle=tau_recycle)
        l23_iins = WangKnoescheCells(step_size=step_size,
                                     max_synaptic_delay=max_synaptic_delay,
                                     init_state=init_states[1],
                                     label='L23_IIns',
                                     synapses=['JansenRitExcitatorySynapse'],
                                     plastic_synapses=[True],
                                     tau_depression=tau_depression,
                                     tau_recycle=tau_recycle)
        l4_eins = WangKnoescheCells(step_size=step_size,
                                    max_synaptic_delay=max_synaptic_delay,
                                    init_state=init_states[2],
                                    label='L4_EINs',
                                    synapses=['JansenRitExcitatorySynapse'],
                                    plastic_synapses=[True],
                                    tau_depression=tau_depression,
                                    tau_recycle=tau_recycle)
        l56_pcs = WangKnoescheCells(step_size=step_size,
                                    max_synaptic_delay=max_synaptic_delay,
                                    init_state=init_states[3],
                                    label='L56_PCs',
                                    tau_depression=tau_depression,
                                    tau_recycle=tau_recycle)
        l56_iins = WangKnoescheCells(step_size=step_size,
                                     max_synaptic_delay=max_synaptic_delay,
                                     init_state=init_states[4],
                                     label='L56_IINs',
                                     synapses=['JansenRitExcitatorySynapse'],
                                     plastic_synapses=[True],
                                     tau_depression=tau_depression,
                                     tau_recycle=tau_recycle)

        N = 5

        # connectivity matrix
        connections = np.zeros((N, N, n_synapses))

        connections[:, :, 0] = [[0., 0., 108., 0., 0.],     # AMPA connections (excitatory)
                                [33.75, 0., 0., 0., 0.],
                                [0., 0., 0., 135., 0.],
                                [135., 0., 0., 0., 0.],
                                [0., 0., 0., 33.75, 0.]]

        connections[:, :, 1] = [[0., 33.75, 0., 0., 0.],    # GABA-A connections (inhibitory)
                                [0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 0.],
                                [0., 0., 0., 0., 33.75],
                                [0., 0., 0., 0., 0.]]

        # delay matrix
        if delays is None:
            delays = np.zeros((N, N))

        # call super init
        #################

        super().__init__(populations=[l23_pcs, l23_iins, l4_eins, l56_pcs, l56_iins],
                         connectivity=connections,
                         delays=delays,
                         step_size=step_size)


#################################################
# moran circuit with spike-frequency adaptation #
#################################################


class MoranCircuit(Circuit):
    """Basic 3-population cortical column circuit as defined in [1]_.

    Parameters
    ----------
    step_size
        Default = 5e-4 s.
    max_synaptic_delay
        Default = None.
    epsilon
        Default = 1e-5 V.
    delays
        Default = None
    init_states
        Default = np.zeros(3)

    See Also
    --------
    :class:`CircuitFromPopulations`: Detailed description of parameters.
    :class:`Circuit`: Detailed description of attributes and methods.

    References
    ----------
    .. [1] R.J. Moran, S.J. Kiebel, K.E. Stephan, R.B. Reilly, J. Daunizeau & K.J. Friston, "A Neural Mass Model of
       Spectral Responses in Electrophysiology" NeuroImage, vol. 37, pp. 706-720, 2007.

    """

    def __init__(self,
                 step_size: float = 5e-4,
                 max_synaptic_delay: Optional[float] = None,
                 epsilon: float = 1e-5,
                 delays: Optional[np.ndarray] = None,
                 init_states: np.ndarray = np.zeros(3)
                 ) -> None:
        """Initializes a basic Moran circuit of pyramidal cells (plastic + non-plastic), excitatory and inhibitory
        interneurons.
        """

        # set parameters
        ################

        population_labels = ['PCs_plastic',
                             'PCs_nonplastic',
                             'EINs',
                             'IINs']
        N = 4

        # synapse information
        n_synapses = 2                                       # excitatory and inhibitory

        # connectivity matrix
        connections = np.zeros((N, N, n_synapses))

        connections[:, :, 0] = [[0., 0., 128., 0.],     # excitatory connections
                                [0., 0., 128., 0.],
                                [128., 0., 0.,  0.],
                                [0., 64., 0., 0.]]

        connections[:, :, 1] = [[0., 0., 0., 64.],      # inhibitory connections
                                [0., 0., 0., 64.],
                                [0., 0., 0., 0.],
                                [0., 0., 0., 16.]]

        # spike-frequency adaptation time constant
        tau = 0.512

        # delays
        if delays is None:
            delays = np.zeros((N, N)) + 2e-3 / step_size

        # synapse params
        synapse_params = {'epsilon': epsilon}

        # instantiate populations
        #########################

        pcs_plastic = MoranPyramidalCells(step_size=step_size,
                                          max_synaptic_delay=max_synaptic_delay,
                                          synapse_params=[synapse_params, synapse_params],
                                          init_state=init_states[0],
                                          tau=tau,
                                          label=population_labels[0]
                                          )
        pcs_nonplastic = MoranPyramidalCells(step_size=step_size,
                                             max_synaptic_delay=max_synaptic_delay,
                                             synapse_params=[synapse_params, synapse_params],
                                             init_state=init_states[0],
                                             label=population_labels[1]
                                             )
        eins = MoranExcitatoryInterneurons(step_size=step_size,
                                           max_synaptic_delay=max_synaptic_delay,
                                           synapse_params=[synapse_params],
                                           init_state=init_states[1],
                                           label=population_labels[2])
        iins = MoranInhibitoryInterneurons(step_size=step_size,
                                           max_synaptic_delay=max_synaptic_delay,
                                           synapse_params=[synapse_params, synapse_params],
                                           init_state=init_states[2],
                                           label=population_labels[3])

        # call super init
        #################

        super().__init__(populations=[pcs_plastic, pcs_nonplastic, eins, iins],
                         connectivity=connections,
                         delays=delays,
                         step_size=step_size)
