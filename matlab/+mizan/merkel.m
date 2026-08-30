function Me = merkel(m_w, m_a, c, n)
%MERKEL Fill thermal characteristic, Me = c*(m_w/m_a)^n.
%   The standard two-parameter empirical form used in CTI/Merkel practice.
%   c and n are the ONLY quantities calibrated from data in the whole
%   thermal model.
Me = c .* (m_w./m_a).^n;
end
