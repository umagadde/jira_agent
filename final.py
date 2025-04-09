import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.colors as mcolors
from matplotlib import patheffects
import numpy as np

def visualize_missing_data(csv_file_path, output_image_path='jira_hygiene_dashboard.png'):
    """
    Creates a beautiful, modern visualization of missing values in specified columns.
    """
    # Read data
    df = pd.read_csv(csv_file_path)
    total_rows = len(df)
    
    # Count missing values
    columns_to_check = ['description', 'acceptance_criteria', 'epic_id']
    missing_counts = {col: df[col].isna().sum() for col in columns_to_check}
    
    # Create figure with beautiful styling
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Add gradient background
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))
    fig.figimage(gradient, cmap='Blues', alpha=0.1, zorder=0)
    
    # Custom colors
    colors = {
        'background': '#ffffff',
        'header': '#2b3a4a',
        'complete': '#4caf50',
        'missing': '#f44336',
        'text': '#333333',
        'highlight': '#ffc107',
        'accent': '#2196f3',
        'border': '#d6e0f0'
    }
    
    # Remove axes
    ax.axis('off')
    
    # Create main container with rounded corners and shadow
    main_box = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                             boxstyle="round,pad=0.02",
                             facecolor=colors['background'],
                             edgecolor=colors['border'],
                             linewidth=2,
                             alpha=0.95)
    ax.add_patch(main_box)
    
    # Add shadow effect
    shadow = FancyBboxPatch((0.055, 0.045), 0.9, 0.9,
                           boxstyle="round,pad=0.02",
                           facecolor='#000000',
                           edgecolor='none',
                           alpha=0.05,
                           zorder=-1)
    ax.add_patch(shadow)
    
    # Add FULL-WIDTH title bar with blue background
    title_box = Rectangle((0.05, 0.82), 0.9, 0.1,
                         facecolor=colors['accent'],
                         edgecolor='none',
                         zorder=3)
    ax.add_patch(title_box)
    
    # Updated title text
    ax.text(0.5, 0.87, "JIRA HYGIENE DASHBOARD",
            ha='center', va='center', 
            fontsize=18, fontweight='bold', 
            color='white',
            path_effects=[patheffects.withStroke(linewidth=3, foreground='#00000020')])
    
    # Subtitle moved down slightly
    ax.text(0.5, 0.78, f"Analysis of missing values across {total_rows:,} records", 
            ha='center', va='center', 
            fontsize=13, color=colors['text'], alpha=0.8)
    
    # Metrics container
    metrics_box = FancyBboxPatch((0.1, 0.28), 0.8, 0.42,
                               boxstyle="round,pad=0.02",
                               facecolor='#ffffff',
                               edgecolor=colors['border'],
                               linewidth=1.5,
                               alpha=0.9)
    ax.add_patch(metrics_box)
    
    # Draw the metrics for each column
    cell_height = 0.12
    start_y = 0.65
    
    for i, (col, count) in enumerate(missing_counts.items()):
        y_pos = start_y - i * (cell_height + 0.02)
        
        # Column name with icon
        ax.text(0.15, y_pos, f"● {col.replace('_', ' ').title()}", 
                ha='left', va='center', 
                fontsize=13, fontweight='bold', color=colors['header'])
        
        # Status indicator
        status_color = colors['missing'] if count > 0 else colors['complete']
        status_text = "Missing" if count > 0 else "Complete"
        
        # Value box with rounded corners
        value_box = FancyBboxPatch((0.55, y_pos-cell_height/2), 0.25, 0.08,
                                  boxstyle="round,pad=0.02",
                                  facecolor=mcolors.to_rgba(status_color, 0.1),
                                  edgecolor=status_color,
                                  linewidth=1.2)
        ax.add_patch(value_box)
        
        # Values
        percentage = (count / total_rows) * 100
        ax.text(0.57, y_pos, f"{count:,} missing ({percentage:.1f}%)", 
                ha='left', va='center', 
                fontsize=12, color=status_color)
    
    # Add summary section (moved up to fit inside main box)
    total_missing = sum(missing_counts.values())
    completeness = (1 - total_missing/(total_rows*3)) * 100  # 3 columns
    
    summary_box = FancyBboxPatch((0.1, 0.12), 0.8, 0.08,  # Adjusted y-position from 0.1 to 0.12
                               boxstyle="round,pad=0.02",
                               facecolor=mcolors.to_rgba(colors['highlight'], 0.2),
                               edgecolor=colors['highlight'],
                               linewidth=1.5)
    ax.add_patch(summary_box)
    
    ax.text(0.5, 0.16, f"TOTAL MISSING VALUES: {total_missing:,}",  # Adjusted y-position from 0.14 to 0.16
            ha='center', va='center', 
            fontsize=12, fontweight='bold', color=colors['header'])
    
    ax.text(0.5, 0.13, f"Overall Data Completeness: {completeness:.1f}%",  # Adjusted y-position from 0.11 to 0.13
            ha='center', va='center', 
            fontsize=12, color=colors['header'])
    
    # Add decorative elements
    ax.plot([0.1, 0.9], [0.75, 0.75], color=colors['border'], linestyle='--', linewidth=1)
    
    # Ensure everything fits
    plt.tight_layout(pad=3)
    
    # Save with high quality
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    
    print(f"Visualization saved to {output_image_path}")

# Example usage
visualize_missing_data('generated_files/output.csv', 'jira_hygiene_dashboard2.png')