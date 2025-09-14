import { NextRequest, NextResponse } from 'next/server';
import { readdir, readFile, stat } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// GET /api/campaigns/[id]/assets
export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  try {
    const campaignId = params.id;
    
    // Look for assets in the pipeline output directory (above the campaign-manager)
    const outputDir = path.join(process.cwd(), '..', 'output');
    
    if (!existsSync(outputDir)) {
      return NextResponse.json({ 
        campaign_id: campaignId,
        total_assets: 0,
        assets: []
      });
    }

    // Check for campaign-specific directory first
    // Try exact match, then try with _001 suffix for versioned campaigns
    let campaignOutputDir = path.join(outputDir, campaignId);
    let assetFiles: string[] = [];
    let searchPath = '';

    if (!existsSync(campaignOutputDir)) {
      // Try with _001 suffix for pipeline versioning
      campaignOutputDir = path.join(outputDir, `${campaignId}_001`);
    }

    if (existsSync(campaignOutputDir)) {
      // Found campaign-specific directory
      searchPath = campaignOutputDir;
      const files = await readdir(campaignOutputDir);
      assetFiles = files.filter(file => 
        file.endsWith('.png') || 
        file.endsWith('.jpg') || 
        file.endsWith('.jpeg') || 
        file.endsWith('.svg') ||
        file.endsWith('.webp')
      );
    } else {
      // Look for files with campaign ID in name across all directories
      const allFiles = await readdir(outputDir);
      const directories = [];
      
      for (const file of allFiles) {
        const fullPath = path.join(outputDir, file);
        const fileStat = await stat(fullPath);
        if (fileStat.isDirectory()) {
          directories.push(file);
        }
      }

      // Search through directories for files containing campaign ID
      for (const dir of directories) {
        const dirPath = path.join(outputDir, dir);
        try {
          const files = await readdir(dirPath);
          const relevantFiles = files.filter(file => 
            file.toLowerCase().includes(campaignId.toLowerCase()) &&
            (file.endsWith('.png') || 
             file.endsWith('.jpg') || 
             file.endsWith('.jpeg') || 
             file.endsWith('.svg') ||
             file.endsWith('.webp'))
          );
          assetFiles.push(...relevantFiles.map(file => `${dir}/${file}`));
        } catch (error) {
          // Skip directories we can't read
          continue;
        }
      }
      searchPath = outputDir;
    }

    // Get file stats for each asset
    const assets = await Promise.all(
      assetFiles.map(async (file) => {
        try {
          const filePath = path.join(searchPath, file);
          const fileStat = await stat(filePath);
          
          // Extract metadata from filename if possible
          const filename = path.basename(file);
          const parts = filename.split('_');
          
          return {
            filename: filename,
            path: `/api/campaigns/${campaignId}/assets/file?path=${encodeURIComponent(file)}`,
            size: fileStat.size,
            modified: fileStat.mtime.toISOString(),
            type: path.extname(filename).substring(1),
            // Try to extract product and format from filename
            product: parts.length > 0 ? parts[0] : 'unknown',
            format: parts.length > 1 ? parts[1] : 'unknown',
            region: parts.length > 2 ? parts[2] : 'unknown'
          };
        } catch (error) {
          console.error(`Error processing asset ${file}:`, error);
          return null;
        }
      })
    );

    // Filter out any null results
    const validAssets = assets.filter(asset => asset !== null);

    return NextResponse.json({
      campaign_id: campaignId,
      total_assets: validAssets.length,
      assets: validAssets,
      search_path: searchPath
    });

  } catch (error) {
    console.error('Error fetching campaign assets:', error);
    return NextResponse.json(
      { error: 'Failed to fetch campaign assets' }, 
      { status: 500 }
    );
  }
}