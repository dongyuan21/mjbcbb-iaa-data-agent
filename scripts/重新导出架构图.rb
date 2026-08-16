#!/usr/bin/env ruby
# encoding: UTF-8
# frozen_string_literal: true

require "open3"
require "pathname"

root = Pathname.new(__dir__).parent
node = ENV.fetch("NODE_BIN", "node")
renderer = root.join("scripts", "渲染Excalidraw.mjs")
abort("缺少渲染器：#{renderer}") unless renderer.file?

sources = Dir[root.join("**", "*.excalidraw").to_s].sort
abort("没有找到可导出的 Excalidraw 源文件") if sources.empty?

sources.each do |source|
  source = source.force_encoding(Encoding::UTF_8).scrub
  output = source.sub(/\.excalidraw\z/, ".png")
  _stdout, stderr, status = Open3.capture3(node, renderer.to_s, source, output)
  abort("导出失败：#{source}\n#{stderr}") unless status.success?
  puts "已导出：#{Pathname.new(output).relative_path_from(root)}"
end
