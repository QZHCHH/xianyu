<template>
  <div class="dashboard">
    <h1>咸鱼自动化工具 - 控制面板</h1>
    
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">
              <i class="el-icon-goods"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.products }}</div>
              <div class="stat-label">商品总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">
              <i class="el-icon-shopping-cart-full"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.orders }}</div>
              <div class="stat-label">订单总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">
              <i class="el-icon-user"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.accounts }}</div>
              <div class="stat-label">账号总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">
              <i class="el-icon-chat-line-square"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.messages }}</div>
              <div class="stat-label">未回复消息</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>近7天销售趋势</span>
          </div>
          <div class="chart-container">
            <div ref="salesChart" class="chart"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>商品类别分布</span>
          </div>
          <div class="chart-container">
            <div ref="categoryChart" class="chart"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <div slot="header" class="clearfix">
            <span>待处理任务</span>
            <el-button style="float: right; padding: 3px 0" type="text">查看全部</el-button>
          </div>
          <el-table :data="tasks" style="width: 100%">
            <el-table-column prop="name" label="任务名称" width="180"></el-table-column>
            <el-table-column prop="type" label="任务类型" width="120"></el-table-column>
            <el-table-column prop="status" label="状态">
              <template slot-scope="scope">
                <el-tag :type="scope.row.status === '待处理' ? 'danger' : 'success'">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button size="mini" type="primary" @click="handleTask(scope.row)">处理</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'Dashboard',
  data() {
    return {
      stats: {
        products: 0,
        orders: 0,
        accounts: 0,
        messages: 0
      },
      tasks: [],
      salesChart: null,
      categoryChart: null
    };
  },
  mounted() {
    this.fetchStats();
    this.fetchTasks();
    this.$nextTick(() => {
      this.initCharts();
    });
  },
  methods: {
    fetchStats() {
      // 从API获取统计数据
      this.$axios.get('/api/stats')
        .then(response => {
          if (response.data.success) {
            this.stats = response.data.stats;
          }
        })
        .catch(error => {
          this.$message.error('获取统计数据失败: ' + error.message);
        });
    },
    fetchTasks() {
      // 从API获取待处理任务
      this.$axios.get('/api/tasks/pending')
        .then(response => {
          if (response.data.success) {
            this.tasks = response.data.tasks;
          }
        })
        .catch(error => {
          this.$message.error('获取任务数据失败: ' + error.message);
        });
    },
    initCharts() {
      // 初始化销售趋势图表
      this.salesChart = echarts.init(this.$refs.salesChart);
      const salesOption = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: [120, 200, 150, 80, 70, 110, 130],
          type: 'line',
          smooth: true
        }]
      };
      this.salesChart.setOption(salesOption);
      
      // 初始化商品类别分布图表
      this.categoryChart = echarts.init(this.$refs.categoryChart);
      const categoryOption = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 10,
          data: ['数码', '服装', '家居', '美妆', '其他']
        },
        series: [
          {
            name: '商品类别',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: 335, name: '数码' },
              { value: 310, name: '服装' },
              { value: 234, name: '家居' },
              { value: 135, name: '美妆' },
              { value: 148, name: '其他' }
            ]
          }
        ]
      };
      this.categoryChart.setOption(categoryOption);
      
      // 监听窗口大小变化，重新调整图表大小
      window.addEventListener('resize', () => {
        this.salesChart.resize();
        this.categoryChart.resize();
      });
    },
    handleTask(task) {
      // 处理任务
      this.$router.push({ path: `/tasks/${task.id}` });
    }
  }
};
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
  color: #409EFF;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style> 