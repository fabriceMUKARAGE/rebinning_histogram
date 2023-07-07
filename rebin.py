import numpy as np
import hist
from hist import Hist

# Function to rebin a histogram
def rebin(histogram, new_bins=None, reltol=None, abstol=None):
    # Check if at least one parameter is provided for rebinning
    if new_bins is None and reltol is None and abstol is None:
        raise ValueError("Either 'new_bins', 'reltol', or 'abstol' must be provided for rebinning.")

    # Process the new bins if provided
    if new_bins is not None:
        if not isinstance(new_bins, list):
            raise ValueError("'new_bins' must be a list or a list of lists.")
        if not all(isinstance(edges, list) for edges in new_bins):
            raise ValueError("If 'new_bins' is a list of lists, each element must be a list of bin edges.")
        # Create a dictionary mapping axis names to the new bin edges
        new_axes_dict = {axis.name: np.asarray(edges) for axis, edges in zip(histogram.axes, new_bins)}
    else:
        new_axes_dict = {}

    # Process each axis of the histogram
    for axis in histogram.axes:
        # If the axis name is not in the new_axes_dict, calculate new edges based on reltol or abstol
        if axis.name not in new_axes_dict:
            if reltol is not None and abstol is not None:
                raise ValueError("Only one of 'reltol' or 'abstol' should be provided.")
            elif reltol is not None:
                # Calculate new edges based on relative tolerance
                rel_edges = np.diff(axis.edges) * reltol
                new_edges = axis.edges[:-1][np.where(rel_edges >= 0)]
                new_edges = np.concatenate([[axis.edges[0]], new_edges, [axis.edges[-1]]])
            elif abstol is not None:
                # Calculate new edges based on absolute tolerance
                new_edges = axis.edges[np.where(np.diff(axis.edges) >= abstol)]
                new_edges = np.concatenate([[axis.edges[0]], new_edges, [axis.edges[-1]]])
            else:
                # No rebinning needed for this axis
                new_edges = axis.edges
            # Update the new_axes_dict with the new edges
            new_axes_dict[axis.name] = new_edges

    # Calculate the new bin indices for each axis
    new_axes_indices = {
        axis.name: np.digitize(histogram.axes[axis.name].centers, new_axes_dict[axis.name]) - 1
        for axis in histogram.axes
    }

    # Define the slices for extracting the rebinned counts
    slices = tuple(
        slice(new_axes_indices[axis.name][i], new_axes_indices[axis.name][i+1] + 1)
        for i, axis in enumerate(histogram.axes)
    )

    # Extract the rebinned counts from the original histogram
    rebinned_counts = histogram.view(flow=True)[slices]

    # If no counts are present in the rebinned histogram, create an empty array with the correct shape
    if rebinned_counts.size == 0:
        rebinned_counts = np.empty(tuple(slice_.stop - slice_.start for slice_ in slices), dtype=histogram.values().dtype)

    # Create a new rebinned histogram with the updated bin edges
    rebinned_hist = Hist(
        *(hist.axis.Variable(new_axes_dict[axis.name]) if axis.name in new_axes_dict else axis for axis in histogram.axes)
    )

    # Update the rebinned histogram with the rebinned counts
    rebinned_hist.view(flow=True)[tuple(slices)] = rebinned_counts.ravel()

    return rebinned_hist

# Function to test the rebin function
def test_rebin():
    h = Hist(hist.axis.Regular(5, -5, 5))

    # Test Case 1
    rebinned_hist1 = rebin(h, new_bins=[[-7, -5, 0, 1]], reltol=0.1, abstol=None)
    assert len(rebinned_hist1.axes) == len([[-7, -5, 0, 1]])
    # Check if the bin edges of the rebinned histogram match the expected values
    for axis, edges in zip(rebinned_hist1.axes, [[-7, -5, 0, 1]]):
        assert np.allclose(axis.edges, np.asarray(edges))
    # Check if the shape of the rebinned histogram values matches the original histogram
    assert len(rebinned_hist1.values().shape) == len(h.values().shape)
    assert rebinned_hist1.values().shape == rebinned_hist1.view().shape
    # Check if the sum of rebinned histogram values matches the sum of original histogram values
    assert np.allclose(rebinned_hist1.values().sum(), h.values().sum())

    # Test Case 2
    rebinned_hist2 = rebin(h, new_bins=[[0, 1, 2.5, 4]], reltol=None, abstol=0.5)
    assert len(rebinned_hist2.axes) == len([[0, 1, 2.5, 4]])
    # Check if the bin edges of the rebinned histogram match the expected values
    for axis, edges in zip(rebinned_hist2.axes, [[0, 1, 2.5, 4]]):
        assert np.allclose(axis.edges, np.asarray(edges))
    # Check if the shape of the rebinned histogram values matches the original histogram
    assert len(rebinned_hist2.values().shape) == len(h.values().shape)
    assert rebinned_hist2.values().shape == rebinned_hist2.view().shape
    # Check if the sum of rebinned histogram values matches the sum of original histogram values
    assert np.allclose(rebinned_hist2.values().sum(), h.values().sum())

    # Test Case 3
    rebinned_hist3 = rebin(h, new_bins=[[-1, 0, 1, 2]], reltol=0.2, abstol=0.1)
    assert len(rebinned_hist3.axes) == len([[-1, 0, 1, 2]])
    # Check if the bin edges of the rebinned histogram match the expected values
    for axis, edges in zip(rebinned_hist3.axes, [[-1, 0, 1, 2]]):
        assert np.allclose(axis.edges, np.asarray(edges))
    # Check if the shape of the rebinned histogram values matches the original histogram
    assert len(rebinned_hist3.values().shape) == len(h.values().shape)
    assert rebinned_hist3.values().shape == rebinned_hist3.view().shape
    # Check if the sum of rebinned histogram values matches the sum of original histogram values
    assert np.allclose(rebinned_hist3.values().sum(), h.values().sum())
    
    
    # Test Case 4
    rebinned_hist4 = rebin(h, new_bins=[[0, 1, 2, 7]], reltol = None, abstol = None )
    assert len(rebinned_hist4.axes) == len([[0, 1, 2, 7]])

    for axis, edges in zip(rebinned_hist4.axes, [[0, 1, 2, 7]]):
        assert np.allclose(axis.edges, np.asarray(edges))

    assert len(rebinned_hist4.values().shape) == len(h.values().shape)
    assert rebinned_hist4.values().shape == rebinned_hist4.view().shape
    assert np.allclose(rebinned_hist4.values().sum(), h.values().sum())
    
    
    # Test Case 5
    rebinned_hist5 = rebin(h, new_bins=[[2,3], [1,2,3], [4,5]], reltol=0.001, abstol=0.001)
    for axis, edges in zip(rebinned_hist5.axes, [[2,3], [1,2,3], [4,5]]):
        assert np.allclose(axis.edges, np.asarray(edges))

    assert len(rebinned_hist5.values().shape) == len(h.values().shape)
    assert rebinned_hist5.values().shape == rebinned_hist5.view().shape
    assert np.allclose(rebinned_hist5.values().sum(), h.values().sum())